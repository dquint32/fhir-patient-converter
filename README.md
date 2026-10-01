# FHIR Patient Data Converter (FHIR CONV2)

[![tests](https://github.com/dquint32/fhir-patient-converter/actions/workflows/tests.yml/badge.svg)](https://github.com/dquint32/fhir-patient-converter/actions/workflows/tests.yml)
![python](https://img.shields.io/badge/python-3.11%2B-blue)
![pydantic](https://img.shields.io/badge/pydantic-v2-e92063)
![FHIR](https://img.shields.io/badge/FHIR-R4%20%7C%20US%20Core-orange)

## Project Overview
This web-based tool is designed to bridge the gap between manual patient intake and digital health standards. It allows healthcare staff to input patient demographics and contact information in either **English or Spanish** and instantly convert that data into a valid **HL7 FHIR R4 Patient Resource**.

The application is built to be compatible with major EHR systems like Epic, Cerner, and Allscripts by following the **US Core Patient Profile**.

---

## 🛠 Features
* **Bilingual Interface**: Full support for English and Spanish speakers.
* **FHIR R4 Mapping**: Converts form fields into a US Core Patient resource (`v4.0.1`).
* **Validation**: Required fields, email and phone formats. The Python package also checks US state codes, ZIP / ZIP+4, and a plausible date of birth.
* **Standards-correct coding**: The MRN is typed `MR` (v2-0203). The emergency contact keeps v2-0131 `C` and adds a coded v3-RoleCode relationship from free text in English or Spanish ("Spouse" → `SPS`, "Madre" → `MTH`).
* **FHIR JSON rules**: No empty arrays, objects or strings, and an HTML-escaped narrative.
* **Syntax Highlighting**: A readable, XSS-safe view of the generated JSON.
* **Export Options**: Copy to the clipboard or download a `.json` file.

---

## 🐍 Python package (`fhir_converter/`)
The same mapping rules, as a typed, tested library and CLI. Use it for batch conversion or backend pipelines.

| Layer | Module | Responsibility |
|---|---|---|
| Ingestion | `fhir_converter.load_records` | JSON file or text → list of records (a single object or an array) |
| Validation | `models.PatientInput` | Pydantic v2 model. Accepts the browser's camelCase keys or snake_case. Immutable. Rejects unknown fields |
| Transformation | `mapping.to_fhir_patient` | `PatientInput` → FHIR Patient dict. Clock and ID generators are injectable for deterministic tests |

```bash
pip install -e ".[test]"
python -m fhir_converter samples/demo_patient.json                  # one Patient
python -m fhir_converter samples/batch_with_errors.json --bundle    # Bundle; bad records reported on stderr
pytest --cov=fhir_converter                                         # 53 tests
```
In a batch, one invalid record never blocks the others. Each record returns either a Patient or a
list of field-level errors. Exit codes: `0` all converted · `1` some invalid · `2` unreadable input.

The tests check the output against the official FHIR R4B model classes (`fhir.resources`).
They also check the FHIR JSON rule that arrays, objects and strings are never empty, which the
library itself does not enforce.

---

## 🏗 Technical Standards Used
* **Standard**: HL7 FHIR R4 (v4.0.1).
* **Profile**: US Core Patient (`StructureDefinition/us-core-patient`).
* **Terminology**: v2-0203 identifier type, v2-0131 contact role, v3-RoleCode relationships, administrative-gender.
* **Identifiers**: Synthetic Patient IDs and MRNs for testing. Replace `MRN_SYSTEM` with your facility's namespace.

---

## 📂 File Structure
* `index.html`, `fhir-converter.css`, `fhir-converter.js`: browser app
* `dq-theme.css`, `dq-theme.js`: shared design system, same look as davidquintana.dev (light/dark)
* `fhir_converter/`: Python package (models / mapping / CLI)
* `tests/`: pytest suite · `samples/`: example input JSON
* `.github/workflows/tests.yml`: CI on Python 3.11–3.13

---

## 🎓 Academic Purpose
<section id="purpose">
    <h3>Purpose of This Site</h3>
    <p>This website was created in partial fulfillment of the CIS 3030 course requirements at MSU Denver.</p>
    <dl>
        <dt>Student Developer</dt>
        <dd>David Quintana</dd>
        <dt>Contact</dt>
        <dd>dquint32@msudenver.edu</dd>
        <dt>Language Preference</dt>
        <dd>English | Spanish</dd>
        <dt>Course Info</dt>
        <dd>CIS 3030 - Web Development</dd>
    </dl>
</section>

---

## 🚀 How to Use
1.  Open `index.html` in any modern web browser.
2.  (Optional) Click **"Load Demo Data"** to see an example of a bilingual patient record.
3.  Fill out the Patient Information, Contact, Address, and Emergency Contact fields.
4.  Click **"Generate FHIR JSON"** to view the compliant output.
5.  Use the **"Download"** or **"Copy"** buttons to export your data.

---

**Disclaimer:** This tool generates synthetic data for educational and interoperability testing purposes. Always ensure HIPAA compliance when handling Protected Health Information (PHI).
