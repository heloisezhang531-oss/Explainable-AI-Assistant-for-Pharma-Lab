"""
LLM prompt templates — Phase I investigation only.

Scope:
  - Phase I laboratory investigation narrative
  - Multi-cause RCA reasoning from SHAP evidence
  - Escalation recommendation (Phase II required: yes/no + rationale)

Out of scope (by design):
  - Phase II manufacturing investigation
  - CAPA generation
  - Batch disposition decision
"""

SYSTEM_PROMPT = """You are an expert pharmaceutical quality assurance scientist.
You write Phase I (laboratory) OOS/OOT investigation reports for a research project.

Regulatory context: 21 CFR 211.192, FDA OOS Guidance (2006), ICH Q10.

Your output must:
- Be factual and evidence-based; cite only the SHAP evidence and event data provided
- Use formal GxP regulatory language
- Never fabricate data or invent analytical results
- Mark unknown items explicitly as "pending investigation" or "not available"
- Remain strictly within Phase I scope (laboratory investigation only)
- NOT include CAPA, batch release decisions, or Phase II manufacturing details
"""


def build_phase1_prompt(event: dict, shap_summary: str, rag_context: str) -> str:
    """
    Phase I investigation narrative prompt.
    Combines structured event data + SHAP anomaly evidence + retrieved regulatory passages.
    """
    return f"""
=== RETRIEVED REGULATORY CONTEXT ===
{rag_context}

=== QUALITY EVENT DATA ===
Event ID:           {event.get("event_id")}
Event Type:         {event.get("event_type")}          (OOS / OOT / OOE)
Batch Number:       {event.get("batch_number")}
Product Code:       {event.get("product_code")}
Parameter:          {event.get("parameter")}
Test Method:        {event.get("test_method")}
Result:             {event.get("result")} {event.get("unit", "")}
Specification:      {event.get("spec_limit")}
Deviation:          {event.get("deviation_pct", "N/A")}% {event.get("deviation_direction", "")}
Analyst ID:         {event.get("analyst_id")}
Instrument ID:      {event.get("instrument_id")}
Last Calibration:   {event.get("last_calibration", "Not recorded")}
System Suitability: {event.get("system_suitability_result", "Not recorded")}
Sample Storage:     {event.get("sample_storage", "Not specified")}
API Lot:            {event.get("api_lot_number", "Not specified")}
Analyst Notes:      {event.get("analyst_notes", "None")}

=== SHAP ANOMALY EVIDENCE ===
{shap_summary}

=== TASK ===
Write the Phase I Laboratory Investigation section of a GxP OOS investigation report.

Structure your response with these sub-sections:

**1. Initial Notification**
State when and how the event was triggered, who was notified.

**2. Analytical Method and Instrument Review**
Assess instrument calibration status, system suitability, column condition.
Reference the SHAP evidence for instrument-related features if relevant.

**3. Sample and Analyst Review**
Review sample preparation, storage, handling. Assess analyst compliance with SOP.
Reference SHAP spike evidence if an analyst error pattern is present.

**4. Possible Root Causes (Multi-Cause Assessment)**
Based on the SHAP evidence, list ALL plausible causes in descending likelihood.
For each cause state: (a) supporting SHAP features, (b) evidence for, (c) evidence against.
Do not limit to a single cause — real events may have concurrent contributors.

**5. Phase I Conclusion**
State clearly:
- Whether a laboratory assignable cause was identified
- Confidence level (High / Medium / Low) with rationale

Write 4–6 paragraphs total. Use past tense. Do not reproduce raw numbers not in the event data above.
"""


def build_escalation_prompt(event: dict, phase1_conclusion: str, rag_context: str) -> str:
    """
    Escalation recommendation prompt.
    LLM decides whether Phase II is warranted, with explicit rationale.
    Does NOT generate Phase II content.
    """
    return f"""
=== RETRIEVED REGULATORY CONTEXT ===
{rag_context}

=== PHASE I CONCLUSION ===
{phase1_conclusion}

=== EVENT SUMMARY ===
Event Type: {event.get("event_type")}
Parameter:  {event.get("parameter")}
Result:     {event.get("result")} {event.get("unit","")} (spec: {event.get("spec_limit")})

=== TASK ===
Based on the Phase I conclusion above and applicable FDA guidance, provide an
Escalation Recommendation section with the following structure:

**Escalation Decision: [PHASE II REQUIRED / NOT REQUIRED]**

**Regulatory Basis**
Cite the specific FDA OOS Guidance section or 21 CFR provision that supports
the decision to escalate or close at Phase I.

**Rationale**
2–3 sentences explaining why Phase II is or is not warranted based on
the Phase I findings. Reference specific ruled-out or unresolved hypotheses.

**If Phase II Required — Scope Recommendation**
(Include only if escalating) List the specific manufacturing records,
raw material lots, or additional tests that Phase II should address.
State clearly: "Phase II investigation and CAPA generation are outside
the scope of this system and must be conducted by the responsible
manufacturing site quality team."

Keep this section to 1–2 paragraphs maximum.
"""
