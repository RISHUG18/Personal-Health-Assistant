#!/usr/bin/env node

/**
 * PDF Report Generator for Testing
 * Generates dummy medical PDF files for testing Person 1's report upload/extraction pipeline
 * 
 * This script creates simple text-based report files with all necessary metadata
 * for testing extraction and alert triggering logic.
 * 
 * Usage:
 *   node generate_test_pdfs.js [--output-dir=./test-pdfs]
 */

const fs = require('fs');
const path = require('path');

// Parse command-line arguments
const args = process.argv.slice(2);
let outputDir = path.join(__dirname, 'test-pdfs');

args.forEach(arg => {
  if (arg.startsWith('--output-dir=')) {
    outputDir = arg.split('=')[1];
  }
});

// Ensure output directory exists
if (!fs.existsSync(outputDir)) {
  fs.mkdirSync(outputDir, { recursive: true });
}

/**
 * Create a dummy medical report file
 */
function createReportFile(filename, reportContent) {
  const filepath = path.join(outputDir, filename);
  fs.writeFileSync(filepath, reportContent);
  return filepath;
}

// Report 1: Thyroid Panel (NORMAL)
const thyroidReport = `THYROID FUNCTION TEST REPORT
=====================================
Laboratory: Diagnostic Health Services
Report Date: 04-Mar-2026
Patient: Rajesh Verma
Age: 58 | Gender: Male | Sample ID: LAB-2026-89456

---TEST RESULTS---
Test Name                   Value    Unit        Reference      Status
TSH (Thyroid Stimulating)   2.4      mIU/L       0.4-4.0        NORMAL
Free T4                     12.8     pmol/L      9.0-18.0       NORMAL
Free T3                     4.2      pmol/L      2.6-5.7        NORMAL
Total T4                    98.5     nmol/L      64-154         NORMAL

CLINICAL INTERPRETATION:
Thyroid function is completely normal. No evidence of hypothyroidism or
hyperthyroidism. Patient does not require thyroid medication adjustment.
Annual follow-up monitoring is recommended.

---NOTES---
Sample collected: 04-Mar-2026, 09:30 AM
Lab Technician: Dr. S. Patel
Authorized By: Dr. Meera Kumar (Chief Lab Officer)
`;

// Report 2: Kidney Function Test (HIGH/CKD)
const kidneyReport = `COMPREHENSIVE METABOLIC PANEL & KIDNEY FUNCTION TEST
===================================================
Laboratory: Metro Diagnostics Center
Report Date: 18-Feb-2026
Patient: Priya Nair
Age: 42 | Gender: Female | Reference: MET-2026-56234

---KIDNEY FUNCTION MARKERS---
Test Name               Value   Unit         Reference      Status
Creatinine              1.3     mg/dL        0.6-1.2        HIGH
BUN                     24      mg/dL        7-20           HIGH
GFR (estimated)         58      mL/min       >60            LOW
Sodium                  138     mEq/L        136-145        NORMAL
Potassium              4.1     mEq/L        3.5-5.0        NORMAL
Phosphorus             3.8     mg/dL        2.5-4.5        NORMAL

---CLINICAL INTERPRETATION---
Mildly elevated creatinine (1.3 mg/dL) and BUN (24 mg/dL) with estimated GFR
of 58 mL/min/1.73m² suggest Stage 2-3A chronic kidney disease. 
Electrolytes remain well-balanced.

RECOMMENDATIONS:
- Consultation with nephrologist
- Dietary sodium restriction (avoid processed foods)
- Adequate hydration
- Avoid NSAID medications
- Repeat testing in 3 months

Lab Technician: Dr. R. Sharma
Authorized By: Dr. Anita Singh (Nephrologist)
Report Generated: 18-Feb-2026
`;

// Report 3: Diabetes Panel (CRITICAL)
const diabetesReport = `DIABETES MANAGEMENT & GLUCOSE MONITORING PANEL
==============================================
Laboratory: Apollo Diagnostics, Pune
Report Date: 22-Jan-2026
Patient: Vikram Singh
Age: 51 | Diabetes Duration: 8 years | Reference: DIAB-2026-34098

---GLUCOSE CONTROL MARKERS---
Test Name                    Value   Unit      Reference       Status
Fasting Blood Glucose        156     mg/dL     70-100          HIGH
Postprandial Glucose (2hr)   238     mg/dL     <140            CRITICAL
HbA1c                        8.9     %         <5.7            HIGH
Glycated Albumin             28      %         <17             HIGH

---LIPID PROFILE (DIABETIC)---
Total Cholesterol            245     mg/dL     <200            HIGH
LDL Cholesterol              165     mg/dL     <100            HIGH
HDL Cholesterol              32      mg/dL     >50             LOW
Triglycerides                285     mg/dL     <150            HIGH

---CLINICAL SUMMARY---
Patient has poorly controlled Type 2 Diabetes with HbA1c of 8.9% (average
glucose >250 mg/dL over 3 months). Significant dyslipidemia present with
elevated LDL and triglycerides, increased risk of cardiovascular complications.

URGENT RECOMMENDATIONS:
1. Review and intensify diabetes medications
2. Consider adding SGLT2 inhibitor or GLP-1 agonist
3. Initiate statin therapy
4. Lifestyle modifications: dietary changes, increase physical activity
5. Referral to Endocrinologist for comprehensive management
6. Screen for microvascular complications (retinopathy, nephropathy)

Lab Technician: Dr. V. Desai
Authorized By: Dr. Arjun Mehta (Endocrinologist)
Report Generated: 22-Jan-2026 13:45
`;

// Generate the files
console.log('🏥 Generating test medical reports...\n');

try {
  createReportFile('Thyroid_Function_Test_Mar2026.txt', thyroidReport);
  console.log('✅ Created: Thyroid_Function_Test_Mar2026.txt');
  
  createReportFile('Kidney_Function_Test_Feb2026.txt', kidneyReport);
  console.log('✅ Created: Kidney_Function_Test_Feb2026.txt');
  
  createReportFile('Diabetes_Monitoring_Panel_Jan2026.txt', diabetesReport);
  console.log('✅ Created: Diabetes_Monitoring_Panel_Jan2026.txt');
  
  console.log(`\n📁 All reports generated in: ${outputDir}`);
  console.log(`📊 Total files created: 3`);
  console.log(`
Test Coverage:
  - Thyroid panel:    NORMAL (no alerts expected)
  - Kidney function:  HIGH (CKD Stage 2-3, kidney impairment alert)
  - Diabetes panel:   CRITICAL (poor glucose control, high CVD risk)
  
✨ Ready for extraction pipeline testing!\n`);
  
} catch (err) {
  console.error(`❌ Error generating reports: ${err.message}`);
  process.exit(1);
}

module.exports = { createReportFile };
