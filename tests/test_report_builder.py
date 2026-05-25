"""Tests for report builder (no docx rendering, just section assembly)."""
import pytest
from unittest.mock import patch, MagicMock
from src.report.sections import make_event_description

EVENT = {
    "event_id": "OOS-001",
    "event_type": "OOS",
    "triggered_at": "2024-01-15T10:00:00",
    "batch_number": "BN001",
    "product_code": "TAB-500",
    "parameter": "Assay",
    "result": 87.5,
    "unit": "%",
    "spec_limit": "95.0 - 105.0",
    "deviation_pct": 25.0,
    "deviation_direction": "LOW",
}


def test_make_event_description_runs():
    from docx import Document
    doc = Document()
    make_event_description(doc, EVENT)
    full_text = " ".join(p.text for p in doc.paragraphs)
    assert "BN001" in full_text
    assert "87.5" in full_text
    assert "25.0%" in full_text
