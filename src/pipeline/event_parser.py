"""
Parse and enrich a quality event dict.
For this project, events originate from the Žagar CSV (via lims_adapter.py),
not a live LIMS system.
"""
from __future__ import annotations
import math
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


class QualityEvent(BaseModel):
    """Validated quality event — canonical schema for the pipeline."""

    # Identity
    event_id:     str
    event_type:   str          # OOS | OOT | OOE
    triggered_at: datetime
    batch_number: str
    product_code: str

    # Test result
    parameter:   str
    test_method: str
    result:      float
    unit:        str = "%"
    spec_limit:  str           # e.g. "95.0 - 105.0"

    # Lab context
    analyst_id:               str
    instrument_id:            str
    last_calibration:         Optional[str] = None
    system_suitability_result: Optional[str] = None
    sample_storage:           Optional[str] = None
    api_lot_number:           Optional[str] = None
    analyst_notes:            Optional[str] = None

    # SHAP / ML fields (populated by pipeline)
    shap_top_features:        Optional[list] = None
    predicted_event_type:     Optional[str]  = None
    class_probabilities:      Optional[dict] = None

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, v: str) -> str:
        allowed = {"OOS", "OOT", "OOE"}
        if v.upper() not in allowed:
            raise ValueError(f"event_type must be one of {allowed}, got {v!r}")
        return v.upper()

    @field_validator("result")
    @classmethod
    def result_must_be_finite(cls, v: float) -> float:
        if not math.isfinite(v):
            raise ValueError("result must be a finite number")
        return v

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


def parse_event(raw: dict) -> QualityEvent:
    return QualityEvent(**raw)


def enrich_event(event: QualityEvent) -> dict:
    """Add derived fields (deviation %, direction, report timestamp)."""
    data = event.model_dump()
    try:
        parts = [float(x.strip()) for x in event.spec_limit.replace(" ", "").split("-")]
        if len(parts) == 2:
            lo, hi = parts
            midpoint   = (lo + hi) / 2
            half_range = (hi - lo) / 2
            data["spec_lower"]       = lo
            data["spec_upper"]       = hi
            data["deviation_pct"]    = round(abs(event.result - midpoint) / half_range * 100, 2)
            data["deviation_direction"] = (
                "HIGH" if event.result > hi else "LOW" if event.result < lo else "WITHIN"
            )
    except (ValueError, AttributeError):
        pass
    data["report_generated_at"] = datetime.utcnow().isoformat()
    return data
