/**
 * ===================================
 * FHIR R4 Patient Data Converter
 * HL7 FHIR Standard Compliant Module
 * ===================================
 * 
 * Purpose: Convert patient intake form data to FHIR R4 Patient Resource
 * Standard: HL7 FHIR R4 (v4.0.1)
 * Interoperability: Epic, Cerner, Allscripts compatible
 */

// ===================================
// Bilingual Translation Module
// ===================================

const translations = {
    en: {
        mainTitle: "FHIR R4 Patient Data Converter",
        mainSubtitle: "Healthcare Interoperability Standard Compliant",
        formTitle: "Patient Information",
        legendDemographics: "Demographics",
        legendContact: "Contact Information",
        legendAddress: "Address",
        legendEmergency: "Emergency Contact",
        labelFirstname: "First Name",
        labelLastname: "Last Name",
        labelDob: "Date of Birth",
        labelGender: "Gender",
        labelPhone: "Phone Number",
        labelEmail: "Email Address",
        labelAddressline: "Street Address",
        labelCity: "City",
        labelState: "State",
        labelPostalcode: "Postal Code",
        labelEmergencyname: "Contact Name",
        labelRelationship: "Relationship",
        labelEmergencyphone: "Contact Phone",
        optionSelect: "Select...",
        optionMale: "Male",
        optionFemale: "Female",
        optionOther: "Other",
        optionUnknown: "Unknown",
        btnDemo: "Load Demo Data",
        btnGenerate: "Generate FHIR JSON",
        btnDownload: "Download JSON",
        btnCopy: "Copy to Clipboard",
        outputTitle: "FHIR R4 JSON Output",
        metaResource: "Resource Type:",
        metaStandard: "FHIR Standard:",
        metaTimestamp: "Generated:",
        footerText: "Built for Healthcare Interoperability | HL7 FHIR R4 Compliant",
        errorRequired: "This field is required",
        errorEmail: "Please enter a valid email address",
        errorPhone: "Please enter a valid phone number",
        successCopy: "JSON copied to clipboard!",
        errorValidation: "Please fill in all required fields correctly"
    },
    es: {
        mainTitle: "Convertidor de Datos de Pacientes FHIR R4",
        mainSubtitle: "Cumple con el Estándar de Interoperabilidad en Salud",
        formTitle: "Información del Paciente",
        legendDemographics: "Datos Demográficos",
        legendContact: "Información de Contacto",
        legendAddress: "Dirección",
        legendEmergency: "Contacto de Emergencia",
        labelFirstname: "Nombre",
        labelLastname: "Apellido",
        labelDob: "Fecha de Nacimiento",
        labelGender: "Género",
        labelPhone: "Número de Teléfono",
        labelEmail: "Correo Electrónico",
        labelAddressline: "Dirección",
        labelCity: "Ciudad",
        labelState: "Estado",
        labelPostalcode: "Código Postal",
        labelEmergencyname: "Nombre del Contacto",
        labelRelationship: "Relación",
        labelEmergencyphone: "Teléfono del Contacto",
        optionSelect: "Seleccionar...",
        optionMale: "Masculino",
        optionFemale: "Femenino",
        optionOther: "Otro",
        optionUnknown: "Desconocido",
        btnDemo: "Cargar Datos de Prueba",
        btnGenerate: "Generar JSON FHIR",
        btnDownload: "Descargar JSON",
        btnCopy: "Copiar al Portapapeles",
        outputTitle: "Salida JSON FHIR R4",
        metaResource: "Tipo de Recurso:",
        metaStandard: "Estándar FHIR:",
        metaTimestamp: "Generado:",
        footerText: "Construido para Interoperabilidad en Salud | Cumple FHIR R4 de HL7",
        errorRequired: "Este campo es obligatorio",
        errorEmail: "Por favor ingrese un correo electrónico válido",
        errorPhone: "Por favor ingrese un número de teléfono válido",
        successCopy: "¡JSON copiado al portapapeles!",
        errorValidation: "Por favor complete todos los campos requeridos correctamente"
    }
};

// ===================================
// State Management
// ===================================

let currentLanguage = 'en';
let currentFhirJson = null;

// ===================================
// FHIR R4 Mapping Module
// ===================================

/**
 * Maps form data to FHIR R4 Patient Resource
 * @param {Object} formData - Raw form data
 * @returns {Object} FHIR R4 compliant Patient resource
 */
function mapToFhirPatient(formData) {
    const fhirPatient = {
        resourceType: "Patient",
        id: generatePatientId(),
        meta: {
            versionId: "1",
            lastUpdated: new Date().toISOString(),
            profile: ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-patient"]
        },
        text: {
            status: "generated",
            div: `<div xmlns="http://www.w3.org/1999/xhtml">Patient: ${formData.firstName} ${formData.lastName}</div>`
        },
        identifier: [
            {
                use: "official",
                system: "urn:oid:2.16.840.1.113883.4.1",
                value: generateMRN()
            }
        ],
        active: true,
        name: [
            {
                use: "official",
                family: formData.lastName,
                given: [formData.firstName]
            }
        ],
        telecom: [],
        gender: formData.gender,
        birthDate: formData.dob,
        address: [],
        contact: []
    };

    // Add phone telecom if provided
    if (formData.phone) {
        fhirPatient.telecom.push({
            system: "phone",
            value: formData.phone,
            use: "home"
        });
    }

    // Add email telecom if provided
    if (formData.email) {
        fhirPatient.telecom.push({
            system: "email",
            value: formData.email,
            use: "home"
        });
    }

    // Add address if provided
    if (formData.addressLine || formData.city || formData.state || formData.postalCode) {
        const address = {
            use: "home",
            type: "both"
        };

        if (formData.addressLine) address.line = [formData.addressLine];
        if (formData.city) address.city = formData.city;
        if (formData.state) address.state = formData.state;
        if (formData.postalCode) address.postalCode = formData.postalCode;
        address.country = "US";

        fhirPatient.address.push(address);
    }

    // Add emergency contact if provided
    if (formData.emergencyName || formData.emergencyPhone) {
        const emergencyContact = {
            relationship: [
                {
                    coding: [
                        {
                            system: "http://terminology.hl7.org/CodeSystem/v2-0131",
                            code: "C",
                            display: formData.emergencyRelationship || "Emergency Contact"
                        }
                    ]
                }
            ]
        };

        if (formData.emergencyName) {
            const nameParts = formData.emergencyName.split(' ');
            emergencyContact.name = {
                family: nameParts[nameParts.length - 1],
                given: nameParts.slice(0, -1)
            };
        }

        if (formData.emergencyPhone) {
            emergencyContact.telecom = [
                {
                    system: "phone",
                    value: formData.emergencyPhone,
                    use: "mobile"
                }
            ];
        }

        fhirPatient.contact.push(emergencyContact);
    }

    return fhirPatient;
}

/**
 * Generate unique patient ID (simulated)
 * In production, this would be assigned by the EHR system
 */
function generatePatientId() {
    return `patient-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Generate Medical Record Number (simulated)
 * In production, this would be assigned by the hospital/clinic
 */
function generateMRN() {
    return `MRN${Math.floor(Math.random() * 900000) + 100000}`;
}

// ===================================
// Validation Module
// ===================================

/**
 * Validates form data before FHIR conversion
 * @param {Object} formData - Form data to validate
 * @returns {Object} Validation result with errors
 */
function validateFormData(formData) {
    const errors = {};

    // Required fields
    if (!formData.firstName || formData.firstName.trim() === '') {
        errors.firstName = translations[currentLanguage].errorRequired;
    }

    if (!formData.lastName || formData.lastName.trim() === '') {
        errors.lastName = translations[currentLanguage].errorRequired;
    }

    if (!formData.dob) {
        errors.dob = translations[currentLanguage].errorRequired;
    }

    if (!formData.gender) {
        errors.gender = translations[currentLanguage].errorRequired;
    }

    // Email validation (if provided)
    if (formData.email && !isValidEmail(formData.email)) {
        errors.email = translations[currentLanguage].errorEmail;
    }

    // Phone validation (if provided)
    if (formData.phone && !isValidPhone(formData.phone)) {
        errors.phone = translations[currentLanguage].errorPhone;
    }

    if (formData.emergencyPhone && !isValidPhone(formData.emergencyPhone)) {
        errors.emergencyPhone = translations[currentLanguage].errorPhone;
    }

    return {
        isValid: Object.keys(errors).length === 0,
        errors
    };
}

/**
 * Email validation helper
 */
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

/**
 * Phone validation helper (accepts various formats)
 */
function isValidPhone(phone) {
    const phoneRegex = /^[\d\s\-\(\)]+$/;
    const digits = phone.replace(/\D/g, '');
    return phoneRegex.test(phone) && digits.length >= 10;
}

/**
 * Display validation errors in the UI
 */
function displayValidationErrors(errors) {
    // Clear all previous errors
    document.querySelectorAll('.error-message').forEach(el => el.textContent = '');
    document.querySelectorAll('input, select').forEach(el => el.classList.remove('error'));

    // Display new errors
    Object.keys(errors).forEach(fieldName => {
        const errorElement = document.getElementById(`${fieldName}-error`);
        const inputElement = document.getElementById(fieldName);

        if (errorElement && inputElement) {
            errorElement.textContent = errors[fieldName];
            inputElement.classList.add('error');
        }
    });
}

/**
 * Clear all validation errors
 */
function clearValidationErrors() {
    document.querySelectorAll('.error-message').forEach(el => el.textContent = '');
    document.querySelectorAll('input, select').forEach(el => el.classList.remove('error'));
}

// ===================================
// UI/DOM Manipulation
// ===================================

/**
 * Collect form data from DOM
 */
function collectFormData() {
    return {
        firstName: document.getElementById('firstName').value.trim(),
        lastName: document.getElementById('lastName').value.trim(),
        dob: document.getElementById('dob').value,
        gender: document.getElementById('gender').value,
        phone: document.getElementById('phone').value.trim(),
        email: document.getElementById('email').value.trim(),
        addressLine: document.getElementById('addressLine').value.trim(),
        city: document.getElementById('city').value.trim(),
        state: document.getElementById('state').value.trim().toUpperCase(),
        postalCode: document.getElementById('postalCode').value.trim(),
        emergencyName: document.getElementById('emergencyName').value.trim(),
        emergencyRelationship: document.getElementById('emergencyRelationship').value.trim(),
        emergencyPhone: document.getElementById('emergencyPhone').value.trim()
    };
}

/**
 * Display FHIR JSON in the output section
 */
function displayFhirJson(fhirObject) {
    const jsonString = JSON.stringify(fhirObject, null, 2);
    const codeElement = document.getElementById('fhir-code');
    
    // Simple syntax highlighting
    const highlighted = jsonString
        .replace(/"([^"]+)":/g, '<span class="json-key">"$1"</span>:')
        .replace(/: "([^"]*)"/g, ': <span class="json-string">"$1"</span>')
        .replace(/: (\d+)/g, ': <span class="json-number">$1</span>')
        .replace(/: (true|false)/g, ': <span class="json-boolean">$1</span>');

    codeElement.innerHTML = highlighted;

    // Show metadata
    const metadataSection = document.getElementById('metadata-section');
    const timestampElement = document.getElementById('meta-timestamp-value');
    timestampElement.textContent = new Date().toLocaleString();
    metadataSection.style.display = 'block';

    // Enable download and copy buttons
    document.getElementById('btn-download').disabled = false;
    document.getElementById('btn-copy').disabled = false;

    // Store current JSON
    currentFhirJson = fhirObject;
}

/**
 * Download FHIR JSON as file
 */
function downloadFhirJson() {
    if (!currentFhirJson) return;

    const jsonString = JSON.stringify(currentFhirJson, null, 2);
    const blob = new Blob([jsonString], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    const timestamp = new Date().toISOString().split('T')[0];
    const filename = `fhir-patient-${timestamp}.json`;
    
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}

/**
 * Copy FHIR JSON to clipboard
 */
async function copyToClipboard() {
    if (!currentFhirJson) return;

    const jsonString = JSON.stringify(currentFhirJson, null, 2);
    
    try {
        await navigator.clipboard.writeText(jsonString);
        alert(translations[currentLanguage].successCopy);
    } catch (err) {
        console.error('Failed to copy:', err);
    }
}

/**
 * Load demo/synthetic data into form
 */
function loadDemoData() {
    document.getElementById('firstName').value = 'María';
    document.getElementById('lastName').value = 'García';
    document.getElementById('dob').value = '1985-03-15';
    document.getElementById('gender').value = 'female';
    document.getElementById('phone').value = '(555) 123-4567';
    document.getElementById('email').value = 'maria.garcia@example.com';
    document.getElementById('addressLine').value = '123 Medical Center Blvd';
    document.getElementById('city').value = 'Los Angeles';
    document.getElementById('state').value = 'CA';
    document.getElementById('postalCode').value = '90001';
    document.getElementById('emergencyName').value = 'Carlos García';
    document.getElementById('emergencyRelationship').value = 'Spouse';
    document.getElementById('emergencyPhone').value = '(555) 987-6543';
    
    // Clear any validation errors
    clearValidationErrors();
}

/**
 * Handle form submission
 */
function handleFormSubmit(event) {
    event.preventDefault();
    
    // Clear previous errors
    clearValidationErrors();
    
    // Collect form data
    const formData = collectFormData();
    
    // Validate form data
    const validation = validateFormData(formData);
    
    if (!validation.isValid) {
        displayValidationErrors(validation.errors);
        alert(translations[currentLanguage].errorValidation);
        return;
    }
    
    // Convert to FHIR
    const fhirPatient = mapToFhirPatient(formData);
    
    // Display result
    displayFhirJson(fhirPatient);
    
    // Scroll to output
    document.getElementById('fhir-converter').scrollIntoView({ 
        behavior: 'smooth',
        block: 'start'
    });
}

// ===================================
// Language Switching
// ===================================

/**
 * Update UI text based on current language
 */
function updateLanguage(lang) {
    currentLanguage = lang;
    const t = translations[lang];
    
    // Update main header
    document.getElementById('main-title').textContent = t.mainTitle;
    document.getElementById('main-subtitle').textContent = t.mainSubtitle;
    
    // Update form title
    document.getElementById('form-title').textContent = t.formTitle;
    
    // Update fieldset legends
    document.getElementById('legend-demographics').textContent = t.legendDemographics;
    document.getElementById('legend-contact').textContent = t.legendContact;
    document.getElementById('legend-address').textContent = t.legendAddress;
    document.getElementById('legend-emergency').textContent = t.legendEmergency;
    
    // Update labels
    document.getElementById('label-firstname').textContent = t.labelFirstname;
    document.getElementById('label-lastname').textContent = t.labelLastname;
    document.getElementById('label-dob').textContent = t.labelDob;
    document.getElementById('label-gender').textContent = t.labelGender;
    document.getElementById('label-phone').textContent = t.labelPhone;
    document.getElementById('label-email').textContent = t.labelEmail;
    document.getElementById('label-addressline').textContent = t.labelAddressline;
    document.getElementById('label-city').textContent = t.labelCity;
    document.getElementById('label-state').textContent = t.labelState;
    document.getElementById('label-postalcode').textContent = t.labelPostalcode;
    document.getElementById('label-emergencyname').textContent = t.labelEmergencyname;
    document.getElementById('label-relationship').textContent = t.labelRelationship;
    document.getElementById('label-emergencyphone').textContent = t.labelEmergencyphone;
    
    // Update select options
    document.getElementById('option-select').textContent = t.optionSelect;
    document.getElementById('option-male').textContent = t.optionMale;
    document.getElementById('option-female').textContent = t.optionFemale;
    document.getElementById('option-other').textContent = t.optionOther;
    document.getElementById('option-unknown').textContent = t.optionUnknown;
    
    // Update buttons
    document.getElementById('btn-demo-text').textContent = t.btnDemo;
    document.getElementById('btn-generate-text').textContent = t.btnGenerate;
    document.getElementById('btn-download-text').textContent = t.btnDownload;
    document.getElementById('btn-copy-text').textContent = t.btnCopy;
    
    // Update output section
    document.getElementById('output-title').textContent = t.outputTitle;
    document.getElementById('meta-resource').textContent = t.metaResource;
    document.getElementById('meta-standard').textContent = t.metaStandard;
    document.getElementById('meta-timestamp').textContent = t.metaTimestamp;
    
    // Update footer
    document.getElementById('footer-text').textContent = t.footerText;
    
    // Update language buttons
    document.querySelectorAll('.lang-btn').forEach(btn => {
        btn.classList.remove('active');
        btn.setAttribute('aria-pressed', 'false');
    });
    
    const activeBtn = document.getElementById(`lang-${lang}`);
    activeBtn.classList.add('active');
    activeBtn.setAttribute('aria-pressed', 'true');
}

// ===================================
// Initialization
// ===================================

/**
 * Initialize application when DOM is ready
 */
document.addEventListener('DOMContentLoaded', function() {
    // Language switching
    document.getElementById('lang-en').addEventListener('click', function() {
        updateLanguage('en');
    });
    
    document.getElementById('lang-es').addEventListener('click', function() {
        updateLanguage('es');
    });
    
    // Demo data button
    document.getElementById('btn-demo').addEventListener('click', loadDemoData);
    
    // Form submission
    document.getElementById('patient-form').addEventListener('submit', handleFormSubmit);
    
    // Download button
    document.getElementById('btn-download').addEventListener('click', downloadFhirJson);
    
    // Copy button
    document.getElementById('btn-copy').addEventListener('click', copyToClipboard);
    
    // Initialize with English
    updateLanguage('en');
    
    console.log('FHIR Patient Data Converter initialized successfully');
});