"""Tests for anomaly injection and labelling."""
import numpy as np
import pandas as pd
import pytest
from src.data.anomaly_injection import (
    inject_point_spike, inject_gradual_drift,
    inject_variance_inflation, inject_step_shift,
    assign_event_labels,
)

def make_df(n=200, seed=0):
    rng = np.random.default_rng(seed)
    return pd.DataFrame({"assay": 100 + rng.normal(0, 2, n)})

def test_spike_creates_oos():
    df = inject_point_spike(make_df(), "assay", rate=0.1, k_range=(4, 5))
    df = assign_event_labels(df, ["assay"])
    assert (df["event_type"] == "OOS").any()

def test_drift_creates_oot():
    df = inject_gradual_drift(make_df(500), "assay", rate=0.008)
    df = assign_event_labels(df, ["assay"])
    assert (df["event_type"].isin(["OOS", "OOT"])).any()

def test_rca_label_set():
    df = inject_point_spike(make_df(), "assay")
    assert "rca_label" in df.columns
    assert (df["rca_label"] == "Lab_Error_Analyst").any()

def test_variance_inflation():
    df = inject_variance_inflation(make_df(400), "assay", scale=4.0)
    df = assign_event_labels(df, ["assay"])
    assert "event_type" in df.columns
