"""Patient intake form -> FHIR R4 Patient converter.

Layers:
    ingestion   load_records()  JSON file/str -> list of raw dicts
    validation  PatientInput    Pydantic v2 model (models.py)
    transform   to_fhir_patient PatientInput -> FHIR Patient dict (mapping.py)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ValidationError

from .mapping import MappingContext, to_fhir_patient
from .models import PatientInput

__all__ = ["ConversionResult", "MappingContext", "PatientInput", "convert", "convert_many",
           "load_records", "to_fhir_patient"]


class RecordError(BaseModel):
    field: str
    message: str


class ConversionResult(BaseModel):
    index: int
    ok: bool
    patient: dict[str, Any] | None = None
    errors: list[RecordError] = []


def load_records(source: str | Path) -> list[dict[str, Any]]:
    """Accept a path or JSON text holding one form object or a list of them."""
    text = Path(source).read_text(encoding="utf-8-sig") if isinstance(source, Path) else source
    data = json.loads(text)
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list) or not all(isinstance(r, dict) for r in data):
        raise ValueError("expected a JSON object or an array of objects")
    return data


def convert(record: dict[str, Any], ctx: MappingContext | None = None,
            index: int = 0) -> ConversionResult:
    """Validate and map one record, returning errors instead of raising."""
    try:
        data = PatientInput.model_validate(record)
    except ValidationError as exc:
        return ConversionResult(index=index, ok=False, errors=[
            RecordError(field=".".join(str(p) for p in e["loc"]) or "record",
                        message=str(e["msg"]).removeprefix("Value error, "))
            for e in exc.errors()
        ])
    return ConversionResult(index=index, ok=True, patient=to_fhir_patient(data, ctx))


def convert_many(records: list[dict[str, Any]],
                 ctx: MappingContext | None = None) -> list[ConversionResult]:
    """One bad record never blocks the rest of the batch."""
    return [convert(r, ctx, i) for i, r in enumerate(records)]
