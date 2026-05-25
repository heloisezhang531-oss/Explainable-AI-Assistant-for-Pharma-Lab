# Knowledge Base Sources

Place these PDFs in `data/raw/` before running `python scripts/build_kb.py`.
All are publicly available from official regulatory bodies.

## Required (OOS Investigation)

| File name | Source | URL |
|---|---|---|
| `fda_oos_guidance_2006.pdf` | FDA CDER | https://www.fda.gov/media/71087/download |
| `21_cfr_211_subpart_j.pdf` | FDA eCFR | https://www.ecfr.gov/current/title-21/part-211/subpart-J |

## Recommended (Quality System)

| File name | Source | URL |
|---|---|---|
| `ich_q10_pharmaceutical_quality.pdf` | ICH | https://www.ich.org/page/quality-guidelines |
| `ich_q9_quality_risk_management.pdf` | ICH | https://www.ich.org/page/quality-guidelines |
| `eu_gmp_chapter6_qc.pdf` | EMA | https://health.ec.europa.eu/medicinal-products/eudralex/eudralex-volume-4_en |

## Optional (Expanded Coverage)

| File name | Source |
|---|---|
| `fda_data_integrity_guidance_2018.pdf` | FDA CDER |
| `ich_q2r2_analytical_validation.pdf` | ICH |
| `pic_s_gmp_guide_pe009.pdf` | PIC/S |

## Adding New Sources

Any additional PDF placed in `data/raw/` will be automatically ingested when
you re-run `build_kb.py`. The chunk overlap ensures context is preserved across
page boundaries.
