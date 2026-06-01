# System Architecture

## Data flow

```
Žagar 2022 Laboratory.csv
        |
  [src/data/loader.py]          Load & validate CSV
        |
  [src/data/anomaly_injection.py]
        |  inject_point_spike()       → OOS → Lab_Error_Analyst
        |  inject_gradual_drift()     → OOT → Process_Drift
        |  inject_variance_inflation()→ OOT → Environmental_Equipment
        |  inject_step_shift()        → OOT → Raw_Material
        |  assign_event_labels()      → OOS / OOT / Normal (z-score + Western Electric)
        |
  [src/ml/features.py]          Engineer features (rolling z, slope, variance ratio, …)
        |
  [src/ml/model.py]             XGBoost: predict event_type (NOT root cause)
        |                       SHAP: quantify per-feature anomaly contribution
        |
  [src/utils/shap_formatter.py] Format SHAP dict → structured text for LLM
        |
  [src/rag/retriever.py]        ChromaDB semantic search over FDA/ICH KB
        |
  [src/rag/prompts.py]          Build section prompts (Phase I + escalation)
        |
  [Claude API]                  Generate Phase I narrative + escalation recommendation
        |
  [src/report/builder.py]       Assemble .docx (cover, event, Phase I, SHAP fig, escalation, sigs)
        |
  Word Report (.docx)  +  Audit Trail (.audit.json)
```

## Module responsibilities

| Module | Responsibility | Does NOT do |
|---|---|---|
| `src/data/` | Load Žagar CSV, inject anomalies, assign labels | Access live LIMS |
| `src/ml/` | Detect anomaly type, quantify feature contributions | Classify root cause |
| `src/rag/` | Retrieve relevant FDA/ICH passages | Generate text |
| `src/pipeline/` | Parse events, coordinate the pipeline | Make batch decisions |
| `src/report/` | Format and save .docx | Phase II / CAPA content |
| `src/utils/` | Logging, audit trail, SHAP formatting | Business logic |

## Key design decision: XGBoost role

XGBoost predicts **event_type** (Normal / OOT / OOS), not root cause.
SHAP values expose *which features* drove the prediction.
The LLM then reasons over those features to propose multi-cause hypotheses.

This split means:
- Model accuracy can be evaluated independently (event-type classification)
- Root cause reasoning is transparent and auditable (LLM reasoning over SHAP)
- The system honestly reflects uncertainty rather than forcing a single label
