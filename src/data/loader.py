"""
Load and validate the Žagar 2022 dataset from data/raw/.
Returns clean DataFrames ready for anomaly injection.
"""
from __future__ import annotations
from pathlib import Path
import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class ZagarDataset:
    """
    Wrapper for the three Žagar 2022 CSV files.

    Attributes
    ----------
    lab : pd.DataFrame       Laboratory measurements (one row = one batch)
    process : pd.DataFrame   Compression time-series (many rows per batch)
    norm : pd.DataFrame      Spec limits / normalization parameters
    """

    def __init__(self, config: dict):
        self.config = config["data"]
        self.lab     = self._load(self.config["laboratory_csv"], "Laboratory")
        self.process = self._load(self.config["process_csv"],    "Process",  required=False)
        self.norm    = self._load(self.config["norm_csv"],       "Normalization", required=False)

    def _load(self, path: str, name: str, required: bool = True) -> pd.DataFrame | None:
        p = Path(path)
        if not p.exists():
            if required:
                raise FileNotFoundError(
                    f"{name} CSV not found at {path}. "
                    "Download from Figshare DOI 10.6084/m9.figshare.c.5645578"
                )
            logger.warning(f"{name} CSV not found at {path} — skipping.")
            return None
        df = pd.read_csv(p)
        logger.info(f"Loaded {name}: {df.shape[0]} rows × {df.shape[1]} cols")
        return df

    @property
    def assay_col(self) -> str:
        """Best-guess column name for API assay in Laboratory.csv."""
        candidates = [c for c in self.lab.columns if "assay" in c.lower() or "api" in c.lower()]
        if not candidates:
            raise ValueError(
                f"Cannot find assay column in {list(self.lab.columns)}. "
                "Set 'data.assay_column' in settings.yaml explicitly."
            )
        return candidates[0]

    def numeric_lab_cols(self) -> list[str]:
        """All numeric columns in Laboratory.csv (exclude batch IDs)."""
        return [c for c in self.lab.select_dtypes(include=[np.number]).columns]
