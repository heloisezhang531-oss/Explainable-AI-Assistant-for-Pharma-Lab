"""
Assembles all sections into a single .docx file using python-docx.
"""
from __future__ import annotations
from pathlib import Path

from docx import Document
from docx.shared import Pt, RGBColor
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

from src.report.sections import (
    make_cover_page,
    make_event_description,
    make_phase1,
    make_phase2,
    make_capa,
    make_conclusion,
    make_signature_block,
    make_disclaimer,
)


class ReportBuilder:
    def __init__(self, config: dict):
        self.config = config

    def build(self, event: dict, sections: dict, out_dir: Path) -> Path:
        doc = Document()
        self._set_default_style(doc)
        self._add_header_footer(doc, event)

        make_cover_page(doc, event)
        make_event_description(doc, event)
        make_phase1(doc, sections["phase1"])
        make_phase2(doc, sections["phase2"])
        make_capa(doc, sections["capa"])
        make_conclusion(doc, sections["conclusion"])
        make_signature_block(doc)
        make_disclaimer(doc, self.config["llm"]["model"])

        filename = (
            f"{event.get('event_type','EVT')}_"
            f"{event.get('batch_number','BATCH')}_"
            f"{event.get('event_id','ID')}_report.docx"
        )
        path = out_dir / filename
        doc.save(str(path))
        return path

    def _set_default_style(self, doc: Document) -> None:
        style = doc.styles["Normal"]
        font = style.font
        font.name = self.config["report"].get("font", "Arial")
        font.size = Pt(11)

    def _add_header_footer(self, doc: Document, event: dict) -> None:
        section = doc.sections[0]

        # Header: watermark text
        header = section.header
        hp = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
        hp.clear()
        run = hp.add_run(
            self.config["report"].get("watermark_text", "AI-ASSISTED DRAFT")
        )
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor(0xCC, 0x00, 0x00)
        run.bold = True

        # Footer: event ID + model
        footer = section.footer
        fp = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
        fp.clear()
        fp.add_run(
            f"Event: {event.get('event_id','')} | "
            f"Model: {self.config['llm']['model']} | "
            "CONFIDENTIAL"
        ).font.size = Pt(8)
