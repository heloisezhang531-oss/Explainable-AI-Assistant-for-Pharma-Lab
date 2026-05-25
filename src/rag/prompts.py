"""
Prompt templates for each report section.
All prompts include a regulatory context block and explicit GxP tone instructions.
"""

SYSTEM_PROMPT = """You are an expert pharmaceutical quality assurance scientist
specializing in GxP-compliant OOS/OOT/Deviation investigation reports.

Your writing must:
- Use formal regulatory language consistent with FDA 21 CFR 211.192 and ICH Q10
- Be factual, evidence-based, and never speculative without qualification
- Acknowledge uncertainty explicitly (e.g., "pending further investigation")
- Avoid conclusions not supported by the provided event data
- Structure content for direct use in a regulated document

You will be given retrieved passages from FDA/ICH guidance as context.
Cite them implicitly in your narrative (do not use footnote numbers).
"""


def build_phase1_prompt(event: dict, context: str) -> str:
    return f"""
=== REGULATORY CONTEXT ===
{context}

=== EVENT DATA ===
Event ID: {event.get("event_id")}
Event Type: {event.get("event_type")}
Parameter: {event.get("parameter")}
Test Method: {event.get("test_method")}
Result: {event.get("result")} {event.get("unit", "")}
Specification: {event.get("spec_limit")}
Analyst ID: {event.get("analyst_id")}
Instrument ID: {event.get("instrument_id")}
Instrument Last Calibration: {event.get("last_calibration")}
System Suitability: {event.get("system_suitability_result", "Not recorded")}
Batch Number: {event.get("batch_number")}
Sample Storage Conditions: {event.get("sample_storage", "Not specified")}

=== TASK ===
Write the Phase I (Laboratory Investigation) section of a pharmaceutical
OOS investigation report. Cover:

1. Initial notification and timeline
2. Review of analyst's technique and documentation
3. Instrument and equipment assessment (calibration, system suitability)
4. Sample integrity review (storage, handling, preparation)
5. Calculation verification
6. Phase I conclusion: confirmed lab error, invalidated, or proceed to Phase II

Write 3-5 formal paragraphs. Use past tense. Do not fabricate data.
"""


def build_phase2_prompt(event: dict, context: str, phase1_conclusion: str) -> str:
    return f"""
=== REGULATORY CONTEXT ===
{context}

=== EVENT DATA ===
{event}

=== PHASE I CONCLUSION ===
{phase1_conclusion}

=== TASK ===
Write the Phase II (Manufacturing/Extended Investigation) section.
Assuming no assignable lab error was found in Phase I, expand the investigation to:

1. Manufacturing batch record review
2. Raw material assessment (lot number, CoA, supplier)
3. Process parameter review (compression, coating, environmental)
4. Historical trend analysis for this product/parameter
5. Similar product/batch assessment
6. Root cause determination with confidence level
7. Impact assessment on released batches

Write 4-6 formal paragraphs. Be explicit about what was ruled out and why.
"""


def build_capa_prompt(event: dict, root_cause: str, context: str) -> str:
    return f"""
=== REGULATORY CONTEXT ===
{context}

=== ROOT CAUSE ===
{root_cause}

=== EVENT ===
Parameter: {event.get("parameter")}
Product: {event.get("product_code", "N/A")}

=== TASK ===
Write the CAPA (Corrective and Preventive Action) section.
Include:
1. Immediate corrective actions taken
2. Root cause-specific preventive actions
3. Effectiveness check criteria and timeline
4. Responsible owner (use generic titles: QC Manager, QA Director)

Be specific and measurable. Avoid vague actions like "retrain staff".
"""


def build_conclusion_prompt(event: dict, root_cause: str, impact: str) -> str:
    return f"""
Write a formal investigation conclusion paragraph for a pharmaceutical
OOS/OOT report. Include:
- Summary of root cause: {root_cause}
- Batch disposition recommendation
- Impact assessment summary: {impact}
- Statement on data integrity (ALCOA+ compliance)
- Signature block placeholder note

Keep to 1-2 paragraphs. Formal regulatory tone.
Event type: {event.get("event_type")}
Parameter: {event.get("parameter")}
"""
