"""Ingestion + validation: the intake form contract as a Pydantic v2 model.

Field names accept the camelCase keys produced by ``collectFormData()`` in
``fhir-converter.js`` (``firstName``, ``postalCode``...) as well as snake_case, so
JSON exported from the browser form can be fed straight into the Python pipeline.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Annotated, Literal

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    EmailStr,
    StringConstraints,
    field_validator,
    model_validator,
)
from pydantic.alias_generators import to_camel

_PHONE_CHARS = re.compile(r"^[\d\s().+\-]+$")
_ZIP = re.compile(r"^\d{5}(-\d{4})?$")

# Two-letter USPS codes (states, DC, territories, military).
US_STATES = frozenset(
    "AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ "
    "NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC PR GU VI AS MP AA AE AP".split()
)


def _blank_to_none(value: object) -> object:
    return None if isinstance(value, str) and not value.strip() else value


def _check_phone(value: str) -> str:
    digits = re.sub(r"\D", "", value)
    if not _PHONE_CHARS.match(value) or not 10 <= len(digits) <= 15:
        raise ValueError("phone number must contain 10-15 digits")
    return value


Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
_Text200 = Annotated[str, StringConstraints(strip_whitespace=True, max_length=200)]
OptText = Annotated[_Text200 | None, BeforeValidator(_blank_to_none)]
OptPhone = Annotated[OptText, AfterValidator(lambda v: _check_phone(v) if v else v)]
OptEmail = Annotated[EmailStr | None, BeforeValidator(_blank_to_none)]

Gender = Literal["male", "female", "other", "unknown"]  # FHIR administrative-gender
_GENDER_SHORTHAND = {"m": "male", "f": "female", "o": "other", "u": "unknown"}


class PatientInput(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True,
        str_strip_whitespace=True, extra="forbid", frozen=True,
    )

    first_name: Name
    last_name: Name
    dob: date
    gender: Gender
    phone: OptPhone = None
    email: OptEmail = None
    address_line: OptText = None
    city: OptText = None
    state: OptText = None
    postal_code: OptText = None
    emergency_name: OptText = None
    emergency_relationship: OptText = None
    emergency_phone: OptPhone = None

    @field_validator("gender", mode="before")
    @classmethod
    def _lower_gender(cls, v: object) -> object:
        if not isinstance(v, str):
            return v
        v = v.strip().lower()
        return _GENDER_SHORTHAND.get(v, v)  # accept HL7 v2 style M/F/O/U

    @field_validator("dob")
    @classmethod
    def _plausible_dob(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("date of birth cannot be in the future")
        if v.year < date.today().year - 130:
            raise ValueError("date of birth is more than 130 years ago")
        return v

    @field_validator("state")
    @classmethod
    def _state(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.upper()
        if v not in US_STATES:
            raise ValueError(f"{v!r} is not a US state/territory code")
        return v

    @field_validator("postal_code")
    @classmethod
    def _zip(cls, v: str | None) -> str | None:
        if v is not None and not _ZIP.match(v):
            raise ValueError("postal code must be a US ZIP (12345 or 12345-6789)")
        return v

    @model_validator(mode="after")
    def _emergency_contact_needs_a_name_or_phone(self) -> "PatientInput":
        if self.emergency_relationship and not (self.emergency_name or self.emergency_phone):
            raise ValueError("emergency relationship given without a contact name or phone")
        return self

    @property
    def has_address(self) -> bool:
        return any((self.address_line, self.city, self.state, self.postal_code))

    @property
    def has_emergency_contact(self) -> bool:
        return bool(self.emergency_name or self.emergency_phone)
