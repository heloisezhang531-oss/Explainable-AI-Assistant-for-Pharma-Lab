"""
Feature engineering for anomaly detection.
Transforms raw Lab CSV columns into signals that expose anomaly fingerprints.
"""
from __future__ import annotations
import numpy as np
import pandas as pd


def engineer_features(df: pd.DataFrame, cols: list[str], window: int = 10) -> pd.DataFrame:
    """
    Build derived features per column:

    Rolling statistics    → detect drift and variance shifts
    Local z-score         → isolate single-batch spikes
    Slope                 → quantify monotonic drift
    Variance ratio        → compare current spread to baseline
    Cross-param z-corr    → fingerprint for instrument-wide errors
    Lot-change flag       → step-shift alignment signal
    """
    df = df.copy()

    for col in cols:
        # ── Rolling mean / std ────────────────────────────────────────────────
        df[f"{col}_roll_mean"] = df[col].rolling(window, min_periods=3).mean()
        df[f"{col}_roll_std"]  = df[col].rolling(window, min_periods=3).std()

        # ── Coefficient of variation ──────────────────────────────────────────
        df[f"{col}_roll_cv"] = (
            df[f"{col}_roll_std"] / df[f"{col}_roll_mean"].abs().replace(0, np.nan)
        )

        # ── Local z-score (deviation from rolling mean) ───────────────────────
        df[f"{col}_local_z"] = (
            (df[col] - df[f"{col}_roll_mean"])
            / df[f"{col}_roll_std"].replace(0, np.nan)
        )

        # ── Drift slope (linear fit over rolling window) ──────────────────────
        df[f"{col}_slope"] = (
            df[col]
            .rolling(window)
            .apply(lambda x: np.polyfit(range(len(x)), x, 1)[0], raw=True)
        )

        # ── Variance ratio: rolling std / baseline std ────────────────────────
        baseline_std = df[col].iloc[:50].std()
        df[f"{col}_var_ratio"] = df[f"{col}_roll_std"] / (baseline_std or 1.0)

    # ── Cross-parameter correlation (instrument error fingerprint) ────────────
    z_cols = [f"z_{c}" for c in cols if f"z_{c}" in df.columns]
    if len(z_cols) > 1:
        df["cross_param_z_corr"] = df[z_cols].apply(lambda r: r.abs().mean(), axis=1)

    # ── Lot-change flag (step-shift detector via consecutive-diff change) ─────
    for col in cols:
        roll_mean = df[f"{col}_roll_mean"]
        df[f"{col}_lot_change_flag"] = (
            roll_mean.diff().abs() > 2.0 * df[f"{col}_roll_std"]
        ).astype(int)

    return df.dropna()


def feature_columns(df: pd.DataFrame, base_cols: list[str]) -> list[str]:
    """Return all engineered feature column names (excludes raw, label, meta cols)."""
    exclude = set(base_cols) | {"event_type", "injection_type", "rca_label"} | {
        c for c in df.columns if c.startswith("z_")
    }
    return [c for c in df.columns if c not in exclude]
