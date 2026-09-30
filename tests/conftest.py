from __future__ import annotations

import itertools
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from fhir_converter import MappingContext

SAMPLES = Path(__file__).resolve().parent.parent / "samples"


@pytest.fixture
def form() -> dict[str, Any]:
    """Same payload as loadDemoData() in fhir-converter.js (camelCase keys)."""
    return json.loads((SAMPLES / "demo_patient.json").read_text(encoding="utf-8"))


@pytest.fixture
def minimal() -> dict[str, Any]:
    return {"firstName": "Ana", "lastName": "Lopez", "dob": "1990-01-01", "gender": "female"}


@pytest.fixture
def ctx() -> MappingContext:
    counter = itertools.count(1)
    return MappingContext(
        now=datetime(2026, 1, 15, 9, 30, tzinfo=timezone.utc),
        new_id=lambda: f"patient-{next(counter)}",
        new_mrn=lambda: "MRN123456",
    )


@pytest.fixture
def samples() -> Path:
    return SAMPLES
