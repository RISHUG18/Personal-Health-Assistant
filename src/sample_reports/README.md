# Sample Lab Reports — Apollo Diagnostics (Synthetic Data)

60 synthetic patient lab reports generated for pipeline testing and UI development.
All data is **entirely fictional** — names, values, and clinical findings are computer-generated.

## Folder Structure

| Folder | Condition | Count |
|---|---|---|
| `healthy/` | All values within normal range | 5 |
| `iron_deficiency/` | Iron Deficiency Anaemia | 5 |
| `diabetes/` | Type 2 Diabetes Mellitus | 5 |
| `high_cholesterol/` | High Cholesterol / Dyslipidaemia | 5 |
| `hypothyroidism/` | Hypothyroidism | 4 |
| `hyperthyroidism/` | Hyperthyroidism | 2 |
| `ckd_early/` | Chronic Kidney Disease (Early, Stage G2-G3) | 3 |
| `liver_disease/` | Elevated Liver Enzymes / NAFLD | 3 |
| `metabolic_syndrome/` | Metabolic Syndrome (DM2+Dyslipidaemia+Obesity) | 5 |
| `vit_d_deficiency/` | Vitamin D Deficiency | 3 |
| `pcos/` | PCOS (Polycystic Ovarian Syndrome) | 3 |
| `cardiac_risk/` | High Cardiac Risk | 3 |
| `multi_condition/` | Multi-condition combinations | 4 |
| `anaemia_b12/` | B12 / Folate Deficiency Anaemia | 3 |
| `autoimmune/` | Autoimmune / Elevated Inflammatory Markers | 2 |
| `pre_diabetes/` | Pre-Diabetes / Impaired Fasting Glucose | 3 |
| `osteoporosis_risk/` | Osteoporosis Risk / Low Bone Density | 2 |

## Filename Convention

```
{category}__{PatientName}__{Age}{GenderCode}.pdf
```

Example: `diabetes__Ramesh_Kumar__52M.pdf`

## Report Structure (per PDF)

Each report is 3 pages:
1. **Page 1** — Complete Blood Count, Iron Studies with flag analysis
2. **Page 2** — Liver Function, Renal Function, Lipid Profile with specialist notes
3. **Page 3** — Thyroid Panel, Diabetes Screening (HbA1c, FBG), Vitamins & Bone, Inflammatory Markers, Clinical Summary

## Patient Demographics Varied

- Age range: 19 — 70 years
- Both Male and Female patients
- BMI range: ~19 (lean) to ~34 (obese)
- Conditions span: single disease, multi-condition, and healthy baselines

## Index File

`report_index.csv` contains all 60 reports with patient name, age, gender, category, filename, and file size.

## Generation

Reports generated using `fpdf2` (Python) with realistic lab reference ranges from standard clinical guidelines (NABL / WHO).
Seed: `random.seed(42)` — reproducible values.

Generator script: `/tmp/generate_reports.py`
