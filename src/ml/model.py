"""
XGBoost anomaly detector + SHAP explainer.

The model predicts event_type (Normal / OOT / OOS) — NOT root cause.
SHAP values are used to surface which features are anomalous and by how much,
feeding into the LLM reasoning step.
"""
from __future__ import annotations
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import shap
from xgboost import XGBClassifier
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """XGBoost wrapper with built-in SHAP explainability."""

    def __init__(self, config: dict):
        self.config    = config
        self.clf       = None
        self.explainer = None
        self.le        = LabelEncoder()
        self.feature_cols: list[str] = []

    # ── training ─────────────────────────────────────────────────────────────

    def fit(self, X: pd.DataFrame, y: pd.Series) -> None:
        """Train with stratified 5-fold CV, class-weight balancing."""
        self.feature_cols = list(X.columns)
        y_enc = self.le.fit_transform(y)

        counts = pd.Series(y_enc).value_counts()
        weights = {i: len(y_enc) / (len(counts) * c) for i, c in counts.items()}
        sample_weights = np.array([weights[yi] for yi in y_enc])

        self.clf = XGBClassifier(
            n_estimators=300,
            max_depth=5,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            eval_metric="mlogloss",
            random_state=42,
            verbosity=0,
        )

        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        for fold, (tr, va) in enumerate(cv.split(X, y_enc)):
            self.clf.fit(
                X.iloc[tr], y_enc[tr],
                sample_weight=sample_weights[tr],
                eval_set=[(X.iloc[va], y_enc[va])],
                verbose=False,
            )
            pred = self.clf.predict(X.iloc[va])
            logger.info(f"Fold {fold+1} report:\n{classification_report(y_enc[va], pred, target_names=self.le.classes_)}")

        self.explainer = shap.TreeExplainer(self.clf)
        logger.info("AnomalyDetector fitted and SHAP explainer ready.")

    def save(self, path: str) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.clf.save_model(path)
        logger.info(f"Model saved: {path}")

    def load(self, path: str) -> None:
        self.clf = XGBClassifier()
        self.clf.load_model(path)
        self.explainer = shap.TreeExplainer(self.clf)
        logger.info(f"Model loaded: {path}")

    # ── inference ────────────────────────────────────────────────────────────

    def predict_single(self, row: pd.Series) -> dict:
        """
        Predict event type + compute SHAP for one batch row.

        Returns
        -------
        dict with keys:
            predicted_event_type : str  (Normal / OOT / OOS)
            class_probabilities  : dict
            shap_values          : dict[feature → shap_value]
            shap_top_features    : list[dict]  top-N by |shap|
        """
        X = pd.DataFrame([row[self.feature_cols]])
        proba = self.clf.predict_proba(X)[0]
        pred_idx = int(np.argmax(proba))
        pred_class = self.le.inverse_transform([pred_idx])[0]

        sv = self.explainer.shap_values(X)
        # sv shape: (n_classes, n_samples, n_features) for multi-class
        shap_for_pred = sv[pred_idx][0] if isinstance(sv, list) else sv[0]

        shap_dict = {col: float(v) for col, v in zip(self.feature_cols, shap_for_pred)}
        top_n = self.config["ml"]["shap_top_n"]
        top_features = sorted(
            [{"feature": k, "shap_value": v, "feature_value": float(row.get(k, 0))}
             for k, v in shap_dict.items()],
            key=lambda x: abs(x["shap_value"]),
            reverse=True,
        )[:top_n]

        return {
            "predicted_event_type": pred_class,
            "class_probabilities":  {c: round(float(p), 3) for c, p in zip(self.le.classes_, proba)},
            "shap_values":          shap_dict,
            "shap_top_features":    top_features,
        }

    def shap_force_plot_png(self, row: pd.Series, output_path: str) -> str:
        """Export SHAP force plot as PNG for embedding in Word report."""
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        X = pd.DataFrame([row[self.feature_cols]])
        sv = self.explainer.shap_values(X)
        pred_idx = int(np.argmax(self.clf.predict_proba(X)[0]))
        shap_for_pred = sv[pred_idx][0] if isinstance(sv, list) else sv[0]

        plt.figure(figsize=(14, 3))
        shap.force_plot(
            self.explainer.expected_value[pred_idx] if hasattr(self.explainer.expected_value, "__len__") else self.explainer.expected_value,
            shap_for_pred,
            X.iloc[0],
            feature_names=self.feature_cols,
            matplotlib=True,
            show=False,
        )
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close()
        return output_path
