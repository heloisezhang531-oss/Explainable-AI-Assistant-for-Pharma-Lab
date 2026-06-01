# Pharma Phase I Investigation Assistant

**Explainable AI for Pharmaceutical Laboratory Quality Events**

Automatically generates GxP-compliant **Phase I laboratory investigation reports** in Word (.docx) format using:
- **XGBoost + SHAP** for anomaly detection and feature-level evidence quantification
- **RAG** over FDA/ICH regulatory documents for grounded context retrieval
- **LLM (Claude)** for multi-cause root cause reasoning and investigation narrative

> **Scope:** Phase I laboratory investigation only. The system outputs an escalation recommendation (Phase II required: yes/no) but does not generate Phase II manufacturing content or CAPA. This reflects the limits of the Žagar 2022 dataset.

---

## Architecture

```
Žagar 2022 Laboratory.csv
        ↓
  Anomaly Injection          inject_point_spike / gradual_drift /
  + Label Assignment         variance_inflation / step_shift  →  OOS / OOT labels
        ↓
  Feature Engineering        rolling z-score, slope, variance ratio,
                             cross-param correlation, lot-change flag
        ↓
  XGBoost + SHAP             predict event_type (NOT root cause)
  ─────────────────          SHAP values → structured anomaly summary
  Role: quantify WHAT        (top-N features with direction & magnitude)
  is anomalous
        ↓
  RAG Retrieval              ChromaDB semantic search
  (FDA/ICH KB)               FDA OOS Guidance, 21 CFR 211, ICH Q10,
                             Warning Letters (as anti-examples)
        ↓
  LLM (Claude)               Phase I narrative  (multi-cause RCA reasoning)
  ─────────────────          Escalation recommendation  (Phase II: yes/no)
  Role: interpret WHY        Input: SHAP summary + RAG passages + event data
        ↓
  Word Report (.docx)        Cover, Event Description, SHAP table + force plot,
  + Audit Trail (.json)      Phase I Investigation, Escalation Recommendation,
                             QC/QA Signature Blocks
```

---

## Repository Structure

```
pharma-rag-investigator/
├── README.md
├── requirements.txt
├── .env.example
│
├── configs/
│   ├── settings.yaml           Model, retrieval, ML, data, report settings
│   └── rca_taxonomy.yaml       Root cause categories with SHAP signals & checklists
│
├── data/
│   ├── raw/                    Žagar 2022 CSVs + FDA/ICH PDFs  (gitignored)
│   ├── processed/              Chunked text for embedding       (auto-generated)
│   └── knowledge_base/         ChromaDB vector store            (auto-generated)
│
├── models/                     Saved XGBoost model (.json)      (auto-generated)
│
├── src/
│   ├── data/
│   │   ├── loader.py           Load & validate Žagar CSV files
│   │   └── anomaly_injection.py Four injection types + label assignment
│   ├── ml/
│   │   ├── features.py         Feature engineering (rolling stats, slope, etc.)
│   │   └── model.py            XGBoost training, SHAP inference, force plot export
│   ├── rag/
│   │   ├── ingestion.py        PDF chunking → ChromaDB
│   │   ├── retriever.py        Semantic search + context formatting
│   │   └── prompts.py          Phase I + escalation prompt templates
│   ├── pipeline/
│   │   ├── event_parser.py     Pydantic validation of quality events
│   │   ├── lims_adapter.py     Žagar CSV row → QualityEvent dict
│   │   └── orchestrator.py     End-to-end pipeline (Phase I only)
│   ├── report/
│   │   └── builder.py          Assemble .docx (no Phase II / CAPA sections)
│   └── utils/
│       ├── audit.py            Companion .audit.json writer
│       ├── logger.py           Logging setup
│       └── shap_formatter.py   SHAP dict → LLM-readable text
│
├── tests/
│   ├── test_event_parser.py
│   ├── test_anomaly_injection.py
│   └── test_shap_formatter.py
│
├── scripts/
│   ├── build_kb.py             Ingest PDFs → ChromaDB  (run once)
│   ├── train_model.py          Train XGBoost on Žagar + injected data
│   └── run_demo.py             Run Phase I pipeline on one event
│
├── notebooks/
│   └── 01_rag_exploration.ipynb
│
└── docs/
    ├── architecture.md         Detailed module responsibilities & data flow
    ├── report_structure.md     Section descriptions, scope boundaries, audit trail
    └── knowledge_sources.md    Which PDFs to download and where
```

---

## Quick Start

### 1. Install

```bash
git clone https://github.com/your-org/pharma-rag-investigator
cd pharma-rag-investigator
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Add ANTHROPIC_API_KEY to .env
```

### 3. Download data

- **Žagar 2022 CSV** → [Figshare DOI 10.6084/m9.figshare.c.5645578](https://figshare.com/collections/Pharmaceutical_tablet_manufacturing/5645578) → place in `data/raw/`
- **FDA/ICH PDFs** → see `docs/knowledge_sources.md` → place in `data/raw/`

### 4. Build knowledge base

```bash
python scripts/build_kb.py
```

### 5. Train anomaly detector

```bash
python scripts/train_model.py
# Trains XGBoost on Žagar + injected anomalies → models/xgb_anomaly.json
```

### 6. Run demo

```bash
# With Žagar data (uses first OOS batch found)
python scripts/run_demo.py

# Without CSV (built-in synthetic event)
python scripts/run_demo.py --static

# Output:
#   reports/OOS_BN240815_OOS-DEMO-001_PhaseI.docx
#   reports/OOS_BN240815_OOS-DEMO-001_PhaseI.audit.json
```

---

## Design Decisions

### Why XGBoost predicts event_type, not root cause

Root cause classification requires causally-grounded labels. Our labels come from injection mechanisms — so the model reliably learns *what pattern of features* leads to an anomaly. SHAP then exposes *which specific features* are anomalous, giving the LLM concrete evidence to reason from rather than accepting a black-box classification.

### Why Phase I only

The Žagar dataset contains process parameters but no manufacturing batch records, deviation logs, or supplier CoA data — the inputs needed for a credible Phase II investigation. Rather than generating hallucinated Phase II content, the system honestly outputs an escalation recommendation with rationale and explicitly defers Phase II to the site quality team.

### Why no CAPA

CAPA generation requires a confirmed, validated root cause — something this system explicitly avoids claiming. CAPA without a verified cause is a compliance risk. The escalation section scopes what Phase II should investigate; CAPA follows from Phase II findings, not from a Phase I draft.

---

## Scope Boundaries

| In scope | Out of scope |
|---|---|
| Phase I lab investigation narrative | Phase II manufacturing investigation |
| Multi-cause RCA reasoning (LLM) | CAPA generation |
| Escalation recommendation (Phase II: yes/no) | Batch disposition decision |
| SHAP feature evidence quantification | Supplier management actions |
| GxP-formatted Word report + audit trail | Real-time LIMS integration |

---

## License

MIT
