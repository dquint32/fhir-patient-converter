from __future__ import annotations

from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from fhir_converter.models import PatientInput


def fields_in_error(exc: ValidationError) -> set[str]:
    return {str(e["loc"][0]) if e["loc"] else "" for e in exc.errors()}


def test_demo_payload_parses_with_camel_case_keys(form) -> None:
    p = PatientInput.model_validate(form)
    assert (p.first_name, p.postal_code, p.state) == ("María", "90001", "CA")


def test_snake_case_keys_are_accepted_too(minimal) -> None:
    p = PatientInput(first_name="Ana", last_name="Lopez", dob=date(1990, 1, 1), gender="female")
    assert p == PatientInput.model_validate(minimal)


@pytest.mark.parametrize("key", ["firstName", "lastName", "dob", "gender"])
def test_required_fields(minimal, key: str) -> None:
    del minimal[key]
    with pytest.raises(ValidationError) as exc:
        PatientInput.model_validate(minimal)
    assert key in fields_in_error(exc.value)


@pytest.mark.parametrize(("key", "value"), [
    ("firstName", "   "),
    ("dob", "1990-02-30"),
    ("dob", (date.today() + timedelta(days=1)).isoformat()),
    ("dob", "1800-01-01"),
    ("gender", "x"),
    ("email", "maria@"),
    ("phone", "555-1234"),
    ("phone", "call me"),
    ("state", "ZZ"),
    ("state", "California"),
    ("postalCode", "9000"),
    ("postalCode", "ABCDE"),
    ("emergencyPhone", "12"),
])
def test_invalid_values(minimal, key: str, value: str) -> None:
    minimal[key] = value
    with pytest.raises(ValidationError) as exc:
        PatientInput.model_validate(minimal)
    assert key in fields_in_error(exc.value)


def test_unknown_keys_are_rejected(minimal) -> None:
    minimal["ssn"] = "123-45-6789"
    with pytest.raises(ValidationError):
        PatientInput.model_validate(minimal)


@pytest.mark.parametrize(("raw", "expected"), [
    ("Female", "female"), (" MALE ", "male"), ("M", "male"), ("f", "female"), ("U", "unknown"),
])
def test_gender_normalisation(minimal, raw: str, expected: str) -> None:
    minimal["gender"] = raw
    assert PatientInput.model_validate(minimal).gender == expected


def test_blank_optional_fields_become_none(minimal) -> None:
    minimal.update(phone="", email="  ", city="", state="", postalCode="")
    p = PatientInput.model_validate(minimal)
    assert p.phone is p.email is p.city is p.state is p.postal_code is None
    assert not p.has_address


def test_state_is_upper_cased_and_zip_plus_four_allowed(minimal) -> None:
    minimal.update(state="co", postalCode="80202-1234")
    p = PatientInput.model_validate(minimal)
    assert (p.state, p.postal_code) == ("CO", "80202-1234")


def test_relationship_without_contact_is_rejected(minimal) -> None:
    minimal["emergencyRelationship"] = "Spouse"
    with pytest.raises(ValidationError, match="relationship"):
        PatientInput.model_validate(minimal)


def test_model_is_immutable(minimal) -> None:
    p = PatientInput.model_validate(minimal)
    with pytest.raises(ValidationError):
        p.first_name = "Changed"  # type: ignore[misc]
