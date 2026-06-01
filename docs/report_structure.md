# Report Structure & Scope

This system generates **Phase I (laboratory) investigation reports only**.

## What IS included

| Section | Content | Regulatory basis |
|---|---|---|
| Event Description | Batch, parameter, result vs spec, SHAP evidence table | 21 CFR 211.192 |
| Phase I Investigation | Analyst, instrument, sample, multi-cause RCA reasoning | FDA OOS Guidance §III.A |
| SHAP Force Plot | Feature contribution figure embedded in report | Explainability evidence |
| Escalation Recommendation | Phase II required: yes/no + rationale + scope | FDA OOS Guidance §III.B |
| Approval Signatures | QC/QA sign-off blocks | 21 CFR Part 11 |

## What is NOT included (by design)

- **Phase II manufacturing investigation** — requires real batch records, not available in Žagar dataset
- **CAPA generation** — requires confirmed root cause from full investigation; outside project scope
- **Batch disposition decision** — must be made by qualified human QA

## Escalation decision logic

The LLM evaluates Phase I findings against FDA OOS Guidance §III.B criteria:
- If assignable lab cause confirmed → Phase I closure (no Phase II)
- If no assignable cause found → Phase II recommended with suggested scope
- The system explicitly states Phase II and CAPA are outside automated scope

## Audit trail (.audit.json)

Generated alongside every .docx. Contains:
- Model version, temperature, timestamp
- All retrieved RAG passages with cosine similarity scores
- SHAP top features for the event
- Section character counts (for drift detection)
