# Pharma RAG Investigator

**Explainable AI Investigation Assistant for Pharmaceutical Quality Events**

Automatically generates GxP-compliant OOS/OOT/Deviation investigation reports
in Word (.docx) format using RAG over FDA guidance and ICH guidelines.

---

## Pipeline

```
Quality Event (from LIMS or manual input)
        |
  [event_parser.py]   Validate & enrich event fields
        |
  [retriever.py]      Semantic search over FDA/ICH knowledge base
        |              (ChromaDB + sentence-transformers)
  [prompts.py]        Build section-specific prompts with context
        |
  [Claude API]        Generate Phase I, Phase II, CAPA, Conclusion text
        |
  [builder.py]        Assemble sections into python-docx document
        |
  Word Report (.docx) + Audit Trail (.audit.json)
```

---

## Repository Structure

```
pharma-rag-investigator/
├── README.md
├── requirements.txt
├── .env.example
|
├── configs/
│   ├── settings.yaml          # Model, retriever, report settings
│   └── rca_taxonomy.yaml      # Root cause categories & checklists
|
├── data/
│   ├── raw/                   # FDA/ICH PDFs (gitignored — see docs/)
│   ├── processed/             # Chunked text (auto-generated)
│   └── knowledge_base/        # ChromaDB vector store (auto-generated)
|
├── src/
│   ├── rag/
│   │   ├── ingestion.py       # PDF chunking & ChromaDB upsert
│   │   ├── retriever.py       # Semantic search, context formatting
│   │   └── prompts.py         # LLM prompt templates (per section)
│   ├── report/
│   │   ├── builder.py         # Assembles .docx from sections
│   │   └── sections.py        # Cover page, Phase I/II, CAPA, sigs
│   ├── pipeline/
│   │   ├── event_parser.py    # Pydantic validation of LIMS events
│   │   └── orchestrator.py    # End-to-end pipeline runner
│   └── utils/
│       ├── audit.py           # Writes companion .audit.json
│       └── logger.py          # Logging setup
|
├── tests/
│   ├── test_event_parser.py
│   ├── test_retriever.py
│   └── test_report_builder.py
|
├── scripts/
│   ├── build_kb.py            # Ingest PDFs → ChromaDB (run once)
│   └── run_demo.py            # Demo with synthetic OOS event
|
├── notebooks/
│   └── 01_rag_exploration.ipynb
|
└── docs/
    ├── knowledge_sources.md   # Which PDFs to download and where
    └── report_structure.md    # Section descriptions & GxP rationale
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
# Add your ANTHROPIC_API_KEY to .env
```

### 3. Add regulatory documents

Download the PDFs listed in `docs/knowledge_sources.md` and place them in `data/raw/`.

### 4. Build the knowledge base

```bash
python scripts/build_kb.py
# Chunks and embeds all PDFs -> data/knowledge_base/
```

### 5. Run the demo

```bash
python scripts/run_demo.py
# Generates: reports/OOS_BN240815_OOS-2024-00815_report.docx
#            reports/OOS_BN240815_OOS-2024-00815_report.audit.json
```

### 6. Run with your own LIMS event

```bash
python scripts/run_demo.py --event path/to/your_event.json
```

---

## LIMS Event JSON Schema

```json
{
  "event_id": "OOS-2024-00815",
  "event_type": "OOS",
  "triggered_at": "2024-08-15T14:32:00",
  "batch_number": "BN240815",
  "product_code": "TAB-500MG-IR",
  "parameter": "Active Ingredient Assay",
  "test_method": "HPLC-UV",
  "result": 87.2,
  "unit": "%",
  "spec_limit": "95.0 - 105.0",
  "analyst_id": "ANA-042",
  "instrument_id": "HPLC-03",
  "last_calibration": "2024-07-14",
  "system_suitability_result": "PASS",
  "sample_storage": "25°C / 60% RH",
  "api_lot_number": "API-2024-L07"
}
```

---

## Tests

```bash
pytest tests/ -v --cov=src
```

---

## GxP Compliance Notes

Every generated report includes:
- Red `AI-ASSISTED DRAFT` watermark in the header
- Model version + timestamp in the footer
- Empty QC/QA signature blocks (Section 6)
- Companion `.audit.json` with model config, retrieved passages, and scores

Reports are not intended for batch release decisions without qualified human review.
All content must be verified against source data before use in a regulated context.

---

## Roadmap

- [ ] XGBoost + SHAP RCA prediction module (Phase 2)
- [ ] Web UI (Streamlit) for non-technical lab staff
- [ ] LIMS webhook integration (auto-trigger on OOS event)
- [ ] Stability trending module (OOT detection)
- [ ] Multi-language report output

---

## License

MIT
