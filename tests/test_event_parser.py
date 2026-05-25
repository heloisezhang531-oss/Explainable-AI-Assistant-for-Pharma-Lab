"""Tests for event parser validation and enrichment."""
import pytest
from pydantic import ValidationError
from src.pipeline.event_parser import parse_event, enrich_event

VALID_EVENT = {
    "event_id": "OOS-2024-001",
    "event_type": "OOS",
    "triggered_at": "2024-01-15T10:00:00",
    "batch_number": "BN001",
    "product_code": "TAB-500",
    "parameter": "Assay",
    "test_method": "HPLC",
    "result": 87.5,
    "unit": "%",
    "spec_limit": "95.0 - 105.0",
    "analyst_id": "ANA-01",
    "instrument_id": "HPLC-01",
}


def test_valid_event_parses():
    event = parse_event(VALID_EVENT)
    assert event.event_type == "OOS"
    assert event.result == 87.5


def test_invalid_event_type_raises():
    bad = {**VALID_EVENT, "event_type": "UNKNOWN"}
    with pytest.raises(ValidationError):
        parse_event(bad)


def test_enrich_adds_deviation_pct():
    event = parse_event(VALID_EVENT)
    enriched = enrich_event(event)
    assert "deviation_pct" in enriched
    assert enriched["deviation_direction"] == "LOW"


def test_non_finite_result_raises():
    bad = {**VALID_EVENT, "result": float("inf")}
    with pytest.raises(ValidationError):
        parse_event(bad)
