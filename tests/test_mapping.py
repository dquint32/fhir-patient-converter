from __future__ import annotations

import json

import pytest
from fhir.resources.R4B.bundle import Bundle
from fhir.resources.R4B.patient import Patient

from fhir_converter import convert, convert_many, load_records
from fhir_converter.cli import main
from fhir_converter.mapping import split_name, to_fhir_patient
from fhir_converter.models import PatientInput


def map_(record, ctx):
    return to_fhir_patient(PatientInput.model_validate(record), ctx)


def find_empty_values(node, path="$"):
    """FHIR JSON rule (hl7.org/fhir/R4/json.html): arrays, objects and strings are never empty.
    fhir.resources does not enforce this, so the tests do."""
    if node in ([], {}, "", None):
        yield path
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from find_empty_values(v, f"{path}[{i}]")
    elif isinstance(node, dict):
        for k, v in node.items():
            yield from find_empty_values(v, f"{path}.{k}")


# ------------------------------------------------------------------ FHIR conformance

def test_full_record_is_valid_fhir(form, ctx) -> None:
    patient = map_(form, ctx)
    Patient.model_validate(patient)
    assert list(find_empty_values(patient)) == []


def test_minimal_record_is_valid_fhir_and_has_no_empty_values(minimal, ctx) -> None:
    patient = map_(minimal, ctx)
    Patient.model_validate(patient)
    assert list(find_empty_values(patient)) == []
    assert not {"telecom", "address", "contact"} & patient.keys()


def test_us_core_required_elements_present(form, ctx) -> None:
    patient = map_(form, ctx)
    assert patient["meta"]["profile"] == ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-patient"]
    assert patient["identifier"] and patient["name"] and patient["gender"]


# ------------------------------------------------------------------ specific mappings

def test_mrn_is_not_labelled_as_a_social_security_number(form, ctx) -> None:
    [identifier] = map_(form, ctx)["identifier"]
    assert identifier["system"] != "urn:oid:2.16.840.1.113883.4.1"
    assert identifier["type"]["coding"][0]["code"] == "MR"
    assert identifier["value"] == "MRN123456"


def test_demographics(form, ctx) -> None:
    patient = map_(form, ctx)
    assert patient["name"] == [{"use": "official", "family": "García", "given": ["María"]}]
    assert (patient["gender"], patient["birthDate"]) == ("female", "1985-03-15")
    assert patient["meta"]["lastUpdated"] == "2026-01-15T09:30:00+00:00"


def test_address(form, ctx) -> None:
    assert map_(form, ctx)["address"] == [{
        "use": "home", "type": "both", "line": ["123 Medical Center Blvd"],
        "city": "Los Angeles", "state": "CA", "postalCode": "90001", "country": "US",
    }]


def test_partial_address_only_includes_given_parts(minimal, ctx) -> None:
    minimal["city"] = "Denver"
    [address] = map_(minimal, ctx)["address"]
    assert address == {"use": "home", "type": "both", "city": "Denver", "country": "US"}


def test_emergency_contact_relationship_codes(form, ctx) -> None:
    [contact] = map_(form, ctx)["contact"]
    emergency, spouse = contact["relationship"]
    assert emergency["coding"][0] == {"system": "http://terminology.hl7.org/CodeSystem/v2-0131",
                                      "code": "C", "display": "Emergency Contact"}
    assert spouse["coding"][0]["code"] == "SPS" and spouse["text"] == "Spouse"
    assert contact["name"]["family"] == "García" and contact["name"]["given"] == ["Carlos"]


@pytest.mark.parametrize(("text", "code"), [("Madre", "MTH"), ("HERMANO", "BRO"), ("friend", "FRND")])
def test_spanish_and_english_relationships(minimal, ctx, text: str, code: str) -> None:
    minimal.update(emergencyName="Rosa Díaz", emergencyRelationship=text)
    relationship = map_(minimal, ctx)["contact"][0]["relationship"]
    assert relationship[1]["coding"][0]["code"] == code


def test_unrecognised_relationship_is_kept_as_text_only(minimal, ctx) -> None:
    minimal.update(emergencyPhone="555-987-6543", emergencyRelationship="Godparent")
    relationship = map_(minimal, ctx)["contact"][0]["relationship"]
    assert relationship[1] == {"text": "Godparent"}


@pytest.mark.parametrize(("full", "expected"), [
    ("Cher", {"text": "Cher", "family": "Cher"}),
    ("Carlos García", {"text": "Carlos García", "family": "García", "given": ["Carlos"]}),
    ("Ana María de León", {"text": "Ana María de León", "family": "León", "given": ["Ana", "María", "de"]}),
])
def test_split_name(full: str, expected: dict) -> None:
    assert split_name(full) == expected


def test_narrative_is_html_escaped(minimal, ctx) -> None:
    minimal["firstName"] = "<script>alert(1)</script>"
    patient = map_(minimal, ctx)
    assert "<script>" not in patient["text"]["div"]
    assert "&lt;script&gt;" in patient["text"]["div"]


# ------------------------------------------------------------------ batch + CLI

def test_convert_returns_errors_instead_of_raising(minimal) -> None:
    minimal["email"] = "bad"
    result = convert(minimal)
    assert not result.ok and result.errors[0].field == "email"


def test_bad_record_does_not_block_batch(samples, ctx) -> None:
    results = convert_many(load_records(samples / "batch_with_errors.json"), ctx)
    assert [r.ok for r in results] == [True, False, True]
    assert {e.field for e in results[1].errors} >= {"firstName", "dob", "email", "state"}


@pytest.mark.parametrize("text", ['"a string"', "[1, 2]", "42"])
def test_load_records_rejects_non_object_json(text: str) -> None:
    with pytest.raises(ValueError):
        load_records(text)


def test_cli_single_record(samples, capsys) -> None:
    assert main([str(samples / "demo_patient.json")]) == 0
    assert json.loads(capsys.readouterr().out)["resourceType"] == "Patient"


def test_cli_bundle_output_is_valid_fhir(samples, tmp_path, capsys) -> None:
    out = tmp_path / "bundle.json"
    assert main([str(samples / "batch_with_errors.json"), "--bundle", "-o", str(out)]) == 1
    bundle = json.loads(out.read_text(encoding="utf-8"))
    Bundle.model_validate(bundle)
    assert len(bundle["entry"]) == 2
    assert "record 1: dob" in capsys.readouterr().err


def test_cli_unreadable_input(tmp_path, capsys) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    assert main([str(bad)]) == 2
    assert main([str(tmp_path / "missing.json")]) == 2
    capsys.readouterr()
