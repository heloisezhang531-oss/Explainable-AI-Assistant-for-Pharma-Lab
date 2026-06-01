"""
Adapter: converts a Žagar 2022 Laboratory.csv row (after anomaly injection)
into the QualityEvent schema.

This is the only place that knows about Žagar-specific column names.
Update _COLUMN_MAP if the actual CSV columns differ from defaults.
"""
from __future__ import annotations
import pandas as pd

# Map Žagar column names → QualityEvent field names
# Adjust keys to match the actual Laboratory.csv headers after download.
_COLUMN_MAP = {
    "assay_col":   "parameter",        # will be filled dynamically
    "impurity":    "impurity_level",
    "water":       "water_content",
    "psd_d90":     "psd_d90",
}


def row_to_event(
    row: pd.Series,
    event_id: str,
    assay_col: str,
    event_type: str,
) -> dict:
    """
    Convert one Žagar Laboratory.csv row to a QualityEvent-compatible dict.

    Parameters
    ----------
    row        : pd.Series  — one batch row (post-injection)
    event_id   : str        — unique ID for this investigation event
    assay_col  : str        — name of the assay column in the row
    event_type : str        — OOS / OOT (from assign_event_labels)
    """
    batch_idx = int(row.name) if hasattr(row, "name") else 0

    return {
        "event_id":     event_id,
        "event_type":   event_type,
        "triggered_at": "2024-01-15T09:00:00",   # static — no real timestamps
        "batch_number": f"BN{batch_idx:04d}",
        "product_code": "TAB-ZAGAR-001",

        # Test result — from the assay column
        "parameter":   "Active Ingredient Assay",
        "test_method": "HPLC-UV",
        "result":      round(float(row[assay_col]), 3),
        "unit":        "%",
        "spec_limit":  "95.0 - 105.0",

        # Lab context — simulated from row index (no real LIMS data)
        "analyst_id":               f"ANA-{(batch_idx % 5) + 1:03d}",
        "instrument_id":            f"HPLC-{(batch_idx % 3) + 1:02d}",
        "last_calibration":         "2024-01-01",
        "system_suitability_result": "PASS",
        "sample_storage":           "25°C / 60% RH",
        "api_lot_number":           f"API-LOT-{(batch_idx // 100) + 1:02d}",
        "analyst_notes":            row.get("analyst_notes", "No anomalies noted."),
    }
