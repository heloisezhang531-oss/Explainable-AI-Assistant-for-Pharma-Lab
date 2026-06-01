"""Tests for event parser — Phase I scope."""
import pytest
from pydantic import ValidationError
from src.pipeline.event_parser import parse_event, enrich_event

VALID = {
    "event_id": "OOS-001", "event_type": "OOS",
    "triggered_at": "2024-01-15T10:00:00",
    "batch_number": "BN001", "product_code": "TAB-500",
    "parameter": "Assay", "test_method": "HPLC",
    "result": 87.5, "unit": "%", "spec_limit": "95.0 - 105.0",
    "analyst_id": "ANA-01", "instrument_id": "HPLC-01",
}

def test_valid():
    e = parse_event(VALID); assert e.event_type == "OOS"

def test_invalid_type():
    with pytest.raises(ValidationError): parse_event({**VALID, "event_type": "UNKNOWN"})

def test_enrich_deviation():
    enriched = enrich_event(parse_event(VALID))
    assert "deviation_pct" in enriched
    assert enriched["deviation_direction"] == "LOW"

def test_ooe_accepted():
    e = parse_event({**VALID, "event_type": "OOE"}); assert e.event_type == "OOE"
