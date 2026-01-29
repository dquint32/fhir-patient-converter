FHIR Patient Data Converter (FHIR CONV2)
Project Overview
This web-based tool is designed to bridge the gap between manual patient intake and digital health standards. It allows healthcare staff to input patient demographics and contact information in either English or Spanish and instantly convert that data into a valid HL7 FHIR R4 Patient Resource.

The application is built to be compatible with major EHR systems like Epic, Cerner, and Allscripts by following the US Core Patient Profile.

🛠 Features
Bilingual Interface: Full support for English and Spanish speakers.

FHIR R4 Mapping: Converts standard form fields into JSON objects compliant with v4.0.1.

Real-time Validation: Validates phone numbers, emails, and required fields before generation.

Syntax Highlighting: Provides a clean, readable view of the generated JSON output.

Export Options: Users can copy the JSON to the clipboard or download it as a .json file for integration testing.

🏗 Technical Standards Used
Standard: HL7 FHIR R4 (v4.0.1).

Profile: US Core Patient (StructureDefinition/us-core-patient).

Identifiers: Automated generation of synthetic Patient IDs and MRNs for testing purposes.

📂 File Structure
index.html: The semantic HTML5 structure of the intake form and output display.

fhir-converter.css: A "Medical Professional" aesthetic with responsive design and accessibility considerations.

fhir-converter.js: The core logic for state management, bilingual translation, and FHIR mapping.

🎓 Academic Purpose
<section id="purpose"> <h3>Purpose of This Site</h3> <p>This website was created in partial fulfillment of the CIS 3030 course requirements at MSU Denver.</p> <dl> <dt>Student Developer</dt> <dd>David Quintana</dd> <dt>Contact</dt> <dd>dquint32@msudenver.edu</dd> <dt>Language Preference</dt> <dd>English | Spanish</dd> </dl> </section>

🚀 How to Use
Open index.html in any modern web browser.

(Optional) Click "Load Demo Data" to see an example of a bilingual patient record.

Fill out the Patient Information, Contact, Address, and Emergency Contact fields.

Click "Generate FHIR JSON" to view the compliant output.

Use the "Download" or "Copy" buttons to export your data.

Disclaimer: This tool generates synthetic data for educational and interoperability testing purposes. Always ensure HIPAA compliance when handling Protected Health Information (PHI).
