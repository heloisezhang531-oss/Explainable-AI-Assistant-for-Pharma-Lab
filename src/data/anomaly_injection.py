"""
Four anomaly injection strategies for Žagar 2022 Laboratory data.
Each function takes a DataFrame and returns an augmented copy with
new columns: injection_type, event_type (OOS/OOT/Normal), rca_label.
"""
from __future__ import annotations
import numpy as np
import pandas as pd


# ── helpers ──────────────────────────────────────────────────────────────────

def _z_label(series: pd.Series, oos_thr: float = 3.0, oot_thr: float = 2.0) -> pd.Series:
    """Assign OOS / OOT / Normal label from z-scores."""
    mu, sigma = series.mean(), series.std()
    z = (series - mu) / sigma
    labels = pd.Series("Normal", index=series.index)
    labels[z.abs() > oos_thr] = "OOS"
    labels[(z.abs() > oot_thr) & (z.abs() <= oos_thr)] = "OOT"
    return labels


def _western_electric_run(z: pd.Series, n: int = 7) -> pd.Series:
    """Return boolean mask where ≥n consecutive points are same-side of mean."""
    above = (z > 0).astype(int)
    run = above.groupby((above != above.shift()).cumsum()).transform("count")
    return run >= n


# ── injection functions ───────────────────────────────────────────────────────

def inject_point_spike(
    df: pd.DataFrame,
    col: str,
    rate: float = 0.05,
    k_range: tuple = (3.5, 6.0),
    seed: int = 42,
) -> pd.DataFrame:
    """
    Single-batch extreme value — simulates analyst error or sample mix-up.
    RCA label: Lab_Error_Analyst
    """
    rng = np.random.default_rng(seed)
    df = df.copy()
    mu, sigma = df[col].mean(), df[col].std()
    idx = rng.choice(df.index, size=int(len(df) * rate), replace=False)
    k    = rng.uniform(*k_range, size=len(idx))
    sign = rng.choice([-1, 1], size=len(idx))
    df.loc[idx, col] = mu + sign * k * sigma
    df.loc[idx, "injection_type"] = "point_spike"
    df.loc[idx, "rca_label"]      = "Lab_Error_Analyst"
    return df


def inject_gradual_drift(
    df: pd.DataFrame,
    col: str,
    rate: float = 0.003,
    start_frac: float = 0.4,
) -> pd.DataFrame:
    """
    Progressive mean shift — simulates column degradation or reagent lot change.
    RCA label: Process_Drift
    """
    df = df.copy().reset_index(drop=True)
    start = int(len(df) * start_frac)
    sigma = df[col].std()
    for i in range(start, len(df)):
        df.loc[i, col] += sigma * rate * (i - start)
    df.loc[start:, "injection_type"] = "gradual_drift"
    df.loc[start:, "rca_label"]      = "Process_Drift"
    return df


def inject_variance_inflation(
    df: pd.DataFrame,
    col: str,
    scale: float = 3.0,
    start_frac: float = 0.5,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Increased spread, stable mean — simulates equipment wear or env instability.
    RCA label: Environmental_Equipment
    """
    rng = np.random.default_rng(seed)
    df = df.copy().reset_index(drop=True)
    start = int(len(df) * start_frac)
    sigma = df[col].std()
    noise = rng.normal(0, scale * sigma, len(df) - start)
    df.loc[start:, col] += noise
    df.loc[start:, "injection_type"] = "variance_inflation"
    df.loc[start:, "rca_label"]      = "Environmental_Equipment"
    return df


def inject_step_shift(
    df: pd.DataFrame,
    col: str,
    delta_sigma: float = 1.8,
    start_frac: float = 0.5,
) -> pd.DataFrame:
    """
    Sudden persistent mean change — simulates raw material supplier lot change.
    RCA label: Raw_Material
    """
    df = df.copy().reset_index(drop=True)
    start = int(len(df) * start_frac)
    delta = delta_sigma * df[col].std()
    df.loc[start:, col] += delta
    df.loc[start:, "injection_type"] = "step_shift"
    df.loc[start:, "rca_label"]      = "Raw_Material"
    return df


# ── label assignment ──────────────────────────────────────────────────────────

def assign_event_labels(
    df: pd.DataFrame,
    cols: list[str],
    oos_thr: float = 3.0,
    oot_thr: float = 2.0,
    run_window: int = 7,
) -> pd.DataFrame:
    """
    Apply statistical rules to assign OOS / OOT / Normal.
    Also adds per-column z-score columns (z_<col>).
    Fills missing injection_type / rca_label as 'none' / 'No_Deviation'.
    """
    df = df.copy()
    if "event_type" not in df.columns:
        df["event_type"] = "Normal"
    if "injection_type" not in df.columns:
        df["injection_type"] = "none"
    if "rca_label" not in df.columns:
        df["rca_label"] = "No_Deviation"

    for col in cols:
        mu, sigma = df[col].mean(), df[col].std()
        z = (df[col] - mu) / (sigma if sigma > 0 else 1)
        df[f"z_{col}"] = z.round(3)

        oos_mask = z.abs() > oos_thr
        oot_mask = (z.abs() > oot_thr) & ~oos_mask
        trend_mask = _western_electric_run(z, run_window) & (df["event_type"] == "Normal")

        df.loc[oos_mask,  "event_type"] = "OOS"
        df.loc[oot_mask & (df["event_type"] != "OOS"), "event_type"] = "OOT"
        df.loc[trend_mask, "event_type"] = "OOT"

    return df


def build_dataset(config: dict, lab_df: pd.DataFrame, target_col: str) -> pd.DataFrame:
    """
    Full pipeline: inject anomalies → assign labels → return augmented DataFrame.
    Uses rates from config['data']['injection'].
    """
    inj = config["data"]["injection"]
    seed = inj.get("random_seed", 42)
    df = lab_df.copy()

    df = inject_point_spike(df,          target_col, rate=inj["point_spike_rate"], seed=seed)
    df = inject_gradual_drift(df,        target_col, rate=inj["gradual_drift_rate"])
    df = inject_variance_inflation(df,   target_col, scale=inj["variance_inflation_scale"], seed=seed + 1)
    df = inject_step_shift(df,           target_col, delta_sigma=inj["step_shift_delta_sigma"])

    numeric_cols = [c for c in df.select_dtypes(include="number").columns
                    if not c.startswith("z_")]
    df = assign_event_labels(
        df, [target_col],
        oos_thr=config["ml"]["oos_z_threshold"],
        oot_thr=config["ml"]["oot_z_threshold"],
    )
    return df
