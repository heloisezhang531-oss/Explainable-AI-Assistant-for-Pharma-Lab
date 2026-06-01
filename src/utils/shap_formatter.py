"""
Format SHAP output into a human-readable string for LLM prompt injection.
"""
from __future__ import annotations


def format_shap_summary(shap_result: dict) -> str:
    """
    Convert shap_result (from AnomalyDetector.predict_single) into
    a structured text block for the LLM prompt.
    """
    if not shap_result:
        return "SHAP analysis not available (model not trained or feature row not provided)."

    lines = [
        f"Predicted event type:  {shap_result.get('predicted_event_type', 'N/A')}",
        f"Class probabilities:   {shap_result.get('class_probabilities', {})}",
        "",
        "Top anomaly-driving features (sorted by |SHAP value|):",
    ]

    top = shap_result.get("shap_top_features", [])
    if not top:
        lines.append("  (no features available)")
    for i, feat in enumerate(top, 1):
        direction = "↑ pushes toward OOS/OOT" if feat["shap_value"] > 0 else "↓ pushes toward Normal"
        lines.append(
            f"  {i}. {feat['feature']:<35} "
            f"SHAP={feat['shap_value']:+.4f}  "
            f"value={feat['feature_value']:.4f}  "
            f"{direction}"
        )

    lines += [
        "",
        "Interpretation guide:",
        "  - High |SHAP| on local_z or roll_std  → single-batch spike (Lab Error pattern)",
        "  - High |SHAP| on cross_param_z_corr   → multiple params co-deviate (Instrument pattern)",
        "  - High |SHAP| on slope feature         → monotonic drift (Process Drift pattern)",
        "  - High |SHAP| on var_ratio             → spread inflation (Equipment/Env pattern)",
        "  - High |SHAP| on lot_change_flag       → step shift after lot change (Raw Material pattern)",
    ]
    return "
".join(lines)
