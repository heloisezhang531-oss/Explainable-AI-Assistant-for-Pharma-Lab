"""
Validates and normalises a LIMS quality event payload into a canonical dict.

LIMS systems vary wildly — this layer absorbs those differences so the rest
of the pipeline always receives a consistent structure.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, validator, Field


class LIMSEvent(BaseModel):
    """Input schema — maps to LIMS JSON export fields."""

    # Identity
    event_id: str
    event_type: str                    # OOS | OOT | OOE | Deviation
    triggered_at: datetime
    batch_number: str
    product_code: str

    # Test result
    parameter: str                     # e.g. "Active Ingredient Assay"
    test_method: str                   # e.g. "HPLC-UV"
    result: float
    unit: str = "%"
    spec_limit: str                    # e.g. "95.0 - 105.0"
    spec_lower: Optional[float] = None
    spec_upper: Optional[float] = None

    # Laboratory context
    analyst_id: str
    instrument_id: str
    last_calibration: Optional[str] = None
    system_suitability_result: Optional[str] = None
    sample_storage: Optional[str] = None

    # Raw material
    api_lot_number: Optional[str] = None
    excipient_lots: Optional[dict] = None

    # Free text
    analyst_notes: Optional[str] = None
    lims_auto_comments: Optional[str] = None

    @validator("event_type")
    def validate_event_type(cls, v: str) -> str:
        allowed = {"OOS", "OOT", "OOE", "Deviation"}
        if v.upper() not in allowed:
            raise ValueError(f"event_type must be one of {allowed}")
        return v.upper()

    @validator("result")
    def result_must_be_finite(cls, v: float) -> float:
        import math
        if not math.isfinite(v):
            raise ValueError("result must be a finite number")
        return v

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


def parse_event(raw: dict) -> LIMSEvent:
    """
    Parse and validate a raw LIMS dict.
    Raises pydantic.ValidationError with clear messages on bad input.
    """
    return LIMSEvent(**raw)


def enrich_event(event: LIMSEvent) -> dict:
    """
    Add derived fields useful downstream (z-score, deviation %, etc.)
    Returns plain dict for easy serialisation.
    """
    data = event.dict()

    # Parse spec limits if numeric
    try:
        parts = event.spec_limit.replace(" ", "").split("-")
        if len(parts) == 2:
            lo, hi = float(parts[0]), float(parts[1])
            midpoint = (lo + hi) / 2
            half_range = (hi - lo) / 2
            data["spec_lower"] = lo
            data["spec_upper"] = hi
            data["deviation_pct"] = round(
                abs(event.result - midpoint) / half_range * 100, 2
            )
            data["deviation_direction"] = "HIGH" if event.result > hi else (
                "LOW" if event.result < lo else "WITHIN"
            )
    except (ValueError, AttributeError):
        pass

    data["report_generated_at"] = datetime.utcnow().isoformat()
    return data
