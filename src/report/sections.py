"""
Section generators: convert raw LLM text + event data into docx Paragraph lists.
Each function returns a list of docx elements ready to append to the document.
"""
from __future__ import annotations
from datetime import datetime

from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH


def make_cover_page(doc, event: dict) -> None:
    """Title block with event metadata."""
    doc.add_paragraph()
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run("PHARMACEUTICAL QUALITY EVENT")
    run.bold = True
    run.font.size = Pt(18)

    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run2 = sub.add_run("INVESTIGATION REPORT")
    run2.bold = True
    run2.font.size = Pt(16)

    doc.add_paragraph()

    meta_table = doc.add_table(rows=8, cols=2)
    meta_table.style = "Table Grid"
    rows_data = [
        ("Event ID",         event.get("event_id", "")),
        ("Event Type",       event.get("event_type", "")),
        ("Batch Number",     event.get("batch_number", "")),
        ("Product Code",     event.get("product_code", "")),
        ("Parameter",        event.get("parameter", "")),
        ("Result / Spec",    f"{event.get('result','')} {event.get('unit','')} / {event.get('spec_limit','')}"),
        ("Triggered At",     str(event.get("triggered_at", ""))[:19]),
        ("Report Generated", datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")),
    ]
    for i, (label, value) in enumerate(rows_data):
        row = meta_table.rows[i]
        row.cells[0].text = label
        row.cells[1].text = value
        row.cells[0].paragraphs[0].runs[0].bold = True

    doc.add_page_break()


def make_event_description(doc, event: dict) -> None:
    doc.add_heading("1. Event Description", level=1)
    p = doc.add_paragraph()
    p.add_run(
        f"On {str(event.get('triggered_at',''))[:10]}, the LIMS system triggered a "
        f"{event.get('event_type')} event for batch {event.get('batch_number')} "
        f"({event.get('product_code')}). The parameter "
        f"“{event.get('parameter')}” yielded a result of "
        f"{event.get('result')} {event.get('unit')} against a specification of "
        f"{event.get('spec_limit')}."
    )
    if event.get("deviation_pct"):
        p.add_run(
            f" This represents a {event['deviation_pct']}% deviation from the "
            f"midpoint of the specification range "
            f"({event.get('deviation_direction', '')} deviation)."
        )


def make_phase1(doc, text: str) -> None:
    doc.add_heading("2. Phase I — Laboratory Investigation", level=1)
    for para in text.strip().split("\n\n"):
        if para.strip():
            doc.add_paragraph(para.strip())


def make_phase2(doc, text: str) -> None:
    doc.add_heading("3. Phase II — Manufacturing / Extended Investigation", level=1)
    for para in text.strip().split("\n\n"):
        if para.strip():
            doc.add_paragraph(para.strip())


def make_capa(doc, text: str) -> None:
    doc.add_heading("4. Corrective and Preventive Actions (CAPA)", level=1)
    for para in text.strip().split("\n\n"):
        if para.strip():
            doc.add_paragraph(para.strip())


def make_conclusion(doc, text: str) -> None:
    doc.add_heading("5. Conclusion and Batch Disposition", level=1)
    for para in text.strip().split("\n\n"):
        if para.strip():
            doc.add_paragraph(para.strip())


def make_signature_block(doc) -> None:
    doc.add_heading("6. Approvals", level=1)
    doc.add_paragraph(
        "This report requires review and approval by qualified QC and QA personnel "
        "prior to use in any batch disposition decision."
    )
    sig_table = doc.add_table(rows=4, cols=3)
    sig_table.style = "Table Grid"
    headers = ["Role", "Name (Print)", "Signature / Date"]
    for j, h in enumerate(headers):
        sig_table.rows[0].cells[j].text = h
        sig_table.rows[0].cells[j].paragraphs[0].runs[0].bold = True
    roles = ["Investigating Analyst", "QC Manager", "QA Reviewer"]
    for i, role in enumerate(roles, 1):
        sig_table.rows[i].cells[0].text = role
        sig_table.rows[i].cells[1].text = ""
        sig_table.rows[i].cells[2].text = ""


def make_disclaimer(doc, model: str) -> None:
    doc.add_paragraph()
    p = doc.add_paragraph()
    run = p.add_run(
        f"AI-ASSISTED DRAFT. Generated using {model}. "
        "All content must be verified by a qualified pharmaceutical professional "
        "before use in any regulated context. This document does not constitute "
        "a batch release decision."
    )
    run.font.size = Pt(9)
    run.font.color.rgb = RGBColor(0x88, 0x88, 0x88)
    run.italic = True
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
