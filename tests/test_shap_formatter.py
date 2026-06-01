"""Tests for SHAP summary formatter."""
from src.utils.shap_formatter import format_shap_summary

MOCK_RESULT = {
    "predicted_event_type": "OOS",
    "class_probabilities": {"Normal": 0.05, "OOT": 0.10, "OOS": 0.85},
    "shap_top_features": [
        {"feature": "assay_local_z", "shap_value": 1.42, "feature_value": 4.1},
        {"feature": "cross_param_z_corr", "shap_value": -0.3, "feature_value": 0.2},
    ],
}

def test_format_contains_event_type():
    s = format_shap_summary(MOCK_RESULT)
    assert "OOS" in s

def test_format_empty():
    s = format_shap_summary({})
    assert "not available" in s.lower()

def test_format_features_listed():
    s = format_shap_summary(MOCK_RESULT)
    assert "assay_local_z" in s
    assert "cross_param_z_corr" in s
