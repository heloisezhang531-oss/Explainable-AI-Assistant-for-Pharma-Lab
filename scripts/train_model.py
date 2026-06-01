"""
Train the XGBoost anomaly detector on Žagar 2022 data + injected anomalies.

Usage:
    python scripts/train_model.py
    python scripts/train_model.py --config configs/settings.yaml
"""
import argparse, logging, sys
sys.path.insert(0, ".")

import yaml
import pandas as pd

from src.data.loader import ZagarDataset
from src.data.anomaly_injection import build_dataset
from src.ml.features import engineer_features, feature_columns
from src.ml.model import AnomalyDetector
from src.utils.logger import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/settings.yaml")
    args = parser.parse_args()

    with open(args.config) as f:
        config = yaml.safe_load(f)

    # 1. Load Žagar data
    dataset = ZagarDataset(config)
    target_col = dataset.assay_col
    logger.info(f"Target column: {target_col}")

    # 2. Inject anomalies + assign labels
    df = build_dataset(config, dataset.lab, target_col)
    logger.info(f"Dataset after injection: {df['event_type'].value_counts().to_dict()}")

    # 3. Feature engineering
    numeric_cols = dataset.numeric_lab_cols()
    df_feat = engineer_features(df, numeric_cols, window=config["ml"].get("rolling_window", 10))

    feat_cols = feature_columns(df_feat, numeric_cols)
    X = df_feat[feat_cols]
    y = df_feat["event_type"]

    logger.info(f"Feature matrix: {X.shape[0]} rows × {X.shape[1]} features")

    # 4. Train
    detector = AnomalyDetector(config)
    detector.fit(X, y)
    detector.feature_cols = feat_cols

    # 5. Save
    detector.save(config["ml"]["model_path"])
    logger.info("Training complete.")


if __name__ == "__main__":
    main()
