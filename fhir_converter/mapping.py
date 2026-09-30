"""Transformation: PatientInput -> FHIR R4 Patient (US Core Patient profile).

Fixes relative to the original ``mapToFhirPatient`` in fhir-converter.js:

* the synthetic MRN was labelled with ``urn:oid:2.16.840.1.113883.4.1``, which is
  the **US Social Security Number** OID; it is now typed ``MR`` under a local system;
* empty arrays (``telecom: []``, ``address: []``, ``contact: []``, ``given: []``) are
  invalid FHIR and are now omitted;
* the emergency-contact relationship put free text such as "Spouse" into the
  ``display`` of v2-0131 code ``C`` ("Emergency Contact"). Now ``C`` keeps its own
  display, and a second, correctly coded v3-RoleCode relationship is added when the
  free text is recognised (English or Spanish);
* names are HTML-escaped before going into the XHTML narrative;
* single-word and multi-word contact names are split safely.
"""

from __future__ import annotations

import html
import secrets
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping

from .models import PatientInput

US_CORE_PATIENT = "http://hl7.org/fhir/us/core/StructureDefinition/us-core-patient"
MRN_SYSTEM = "http://hospital.example.org/fhir/mrn"   # replace with the facility's MRN namespace
V2_0203 = "http://terminology.hl7.org/CodeSystem/v2-0203"
V2_0131 = "http://terminology.hl7.org/CodeSystem/v2-0131"
V3_ROLE_CODE = "http://terminology.hl7.org/CodeSystem/v3-RoleCode"

# Free-text relationship (EN/ES, lower-case) -> (v3-RoleCode, display)
RELATIONSHIPS: Mapping[str, tuple[str, str]] = MappingProxyType({
    "spouse": ("SPS", "spouse"), "esposo": ("SPS", "spouse"), "esposa": ("SPS", "spouse"),
    "husband": ("HUSB", "husband"), "wife": ("WIFE", "wife"),
    "partner": ("DOMPART", "domestic partner"), "pareja": ("DOMPART", "domestic partner"),
    "mother": ("MTH", "mother"), "madre": ("MTH", "mother"),
    "father": ("FTH", "father"), "padre": ("FTH", "father"),
    "parent": ("PRN", "parent"),
    "son": ("SON", "natural son"), "hijo": ("SON", "natural son"),
    "daughter": ("DAU", "natural daughter"), "hija": ("DAU", "natural daughter"),
    "child": ("CHILD", "child"),
    "brother": ("BRO", "brother"), "hermano": ("BRO", "brother"),
    "sister": ("SIS", "sister"), "hermana": ("SIS", "sister"),
    "sibling": ("SIB", "sibling"),
    "friend": ("FRND", "unrelated friend"), "amigo": ("FRND", "unrelated friend"),
    "amiga": ("FRND", "unrelated friend"),
    "neighbor": ("NBOR", "neighbor"), "vecino": ("NBOR", "neighbor"), "vecina": ("NBOR", "neighbor"),
})

Resource = dict[str, Any]


@dataclass(frozen=True)
class MappingContext:
    """Injectable clock and identifier generators (deterministic in tests)."""

    now: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    new_id: Callable[[], str] = field(default=lambda: str(uuid.uuid4()))
    new_mrn: Callable[[], str] = field(default=lambda: f"MRN{secrets.randbelow(900_000) + 100_000}")


def split_name(full: str) -> dict[str, Any]:
    """'Carlos García' -> family García, given [Carlos]; single words become family only."""
    parts = full.split()
    human: dict[str, Any] = {"text": full}
    if parts:
        human["family"] = parts[-1]
    if len(parts) > 1:
        human["given"] = parts[:-1]
    return human


def _relationship(text: str | None) -> list[dict]:
    rel = [{"coding": [{"system": V2_0131, "code": "C", "display": "Emergency Contact"}]}]
    if text:
        coded = RELATIONSHIPS.get(text.strip().lower())
        concept: dict[str, Any] = {"text": text}
        if coded:
            concept["coding"] = [{"system": V3_ROLE_CODE, "code": coded[0], "display": coded[1]}]
        rel.append(concept)
    return rel


def to_fhir_patient(data: PatientInput, ctx: MappingContext | None = None) -> Resource:
    ctx = ctx or MappingContext()
    display_name = f"{data.first_name} {data.last_name}"

    patient: Resource = {
        "resourceType": "Patient",
        "id": ctx.new_id(),
        "meta": {
            "versionId": "1",
            "lastUpdated": ctx.now.isoformat(timespec="seconds"),
            "profile": [US_CORE_PATIENT],
        },
        "text": {
            "status": "generated",
            "div": f'<div xmlns="http://www.w3.org/1999/xhtml">Patient: {html.escape(display_name)}</div>',
        },
        "identifier": [{
            "use": "usual",
            "type": {"coding": [{"system": V2_0203, "code": "MR", "display": "Medical record number"}]},
            "system": MRN_SYSTEM,
            "value": ctx.new_mrn(),
        }],
        "active": True,
        "name": [{"use": "official", "family": data.last_name, "given": [data.first_name]}],
        "gender": data.gender,
        "birthDate": data.dob.isoformat(),
    }

    telecom = []
    if data.phone:
        telecom.append({"system": "phone", "value": data.phone, "use": "home"})
    if data.email:
        telecom.append({"system": "email", "value": str(data.email), "use": "home"})
    if telecom:
        patient["telecom"] = telecom

    if data.has_address:
        address: dict[str, Any] = {"use": "home", "type": "both"}
        if data.address_line:
            address["line"] = [data.address_line]
        for key, value in (("city", data.city), ("state", data.state),
                           ("postalCode", data.postal_code)):
            if value:
                address[key] = value
        address["country"] = "US"
        patient["address"] = [address]

    if data.has_emergency_contact:
        contact: dict[str, Any] = {"relationship": _relationship(data.emergency_relationship)}
        if data.emergency_name:
            contact["name"] = split_name(data.emergency_name)
        if data.emergency_phone:
            contact["telecom"] = [{"system": "phone", "value": data.emergency_phone, "use": "mobile"}]
        patient["contact"] = [contact]

    return patient
