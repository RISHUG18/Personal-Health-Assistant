"""
Demo personas for HealthCompanion.

Three pre-defined identities used across demos, seed scripts, and test fixtures:
  - PERSONA_MEERA   patient · 28F · iron-deficiency anaemia
  - PERSONA_RAJAN   patient · 55M · Type 2 diabetes + hypertension
  - PERSONA_DR_MEHTA doctor · cardiologist

Each persona carries:
  - Stable mock user_id (usable as the `user_id` field in API calls)
  - Demographic and clinical background
  - A curated list of demo questions that exercise different RAG paths
  - A reference to the most representative sample PDF in sample_reports/
"""

from dataclasses import dataclass, field
from typing import List, Literal

Role = Literal["patient", "doctor"]
Gender = Literal["M", "F"]


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class PatientPersona:
    id: str                          # stable mock user_id for API calls
    name: str
    age: int
    gender: Gender
    city: str
    occupation: str
    conditions: List[str]            # confirmed diagnoses / clinical findings
    current_medications: List[str]
    recent_reports: List[str]        # filenames relative to sample_reports/
    demo_questions: List[str]        # questions that showcase different RAG paths
    role: Role = "patient"


@dataclass
class DoctorPersona:
    id: str                          # stable mock user_id for API calls
    name: str
    specialization: str
    hospital: str
    years_experience: int
    manages_patients: List[str]      # list of patient persona ids this doctor covers
    demo_questions: List[str]
    role: Role = "doctor"


# ── Persona 1 — Meera Iyer (28F, iron-deficiency anaemia) ────────────────────

PERSONA_MEERA = PatientPersona(
    id="demo-user-meera-001",
    name="Meera Iyer",
    age=28,
    gender="F",
    city="Chennai",
    occupation="Software Engineer",
    conditions=[
        "Iron Deficiency Anaemia (Hb 9.8 g/dL, Ferritin 7 ng/mL)",
        "Vitamin D Insufficiency (18 ng/mL)",
        "Sedentary lifestyle — avg 3,200 steps/day",
        "Chronic mild sleep deprivation (5.5–6 hrs/night)",
    ],
    current_medications=[
        "Ferrous Sulcate 200 mg OD",
        "Vitamin D3 60,000 IU weekly supplement",
    ],
    recent_reports=[
        "iron_deficiency/iron_deficiency__Riya_Sharma__28F.pdf",
        "vit_d_deficiency/vit_d_deficiency__Aishwarya_Patel__26F.pdf",
    ],
    demo_questions=[
        # Lab interpretation
        "What does my latest haemoglobin reading of 9.8 g/dL mean?",
        "My ferritin is 7 ng/mL — is that dangerously low?",
        "Can you compare my iron levels from January and March?",
        # Lifestyle & nutrition
        "What foods should I eat to raise my ferritin naturally?",
        "Will iron supplements cause constipation?",
        # Trend / wearable
        "How has my sleep changed over the past week?",
        "My step count today was only 2,400 — is that a problem?",
        # Environment
        "Is today's AQI in Chennai safe for an evening run?",
        "Does poor air quality make anaemia symptoms worse?",
        # Summary
        "Give me a plain-English summary of my blood report from last Tuesday.",
    ],
)

# ── Persona 2 — Rajan Subramaniam (55M, DM2 + hypertension) ─────────────────

PERSONA_RAJAN = PatientPersona(
    id="demo-user-rajan-002",
    name="Rajan Subramaniam",
    age=55,
    gender="M",
    city="Bengaluru",
    occupation="Retired Bank Manager",
    conditions=[
        "Type 2 Diabetes Mellitus (HbA1c 8.4%, FBG 162 mg/dL)",
        "Hypertension (BP 148/96 mmHg)",
        "Dyslipidaemia (LDL 178 mg/dL, TG 240 mg/dL)",
        "Overweight (BMI 28.3)",
        "Early diabetic nephropathy (eGFR 58 mL/min, microalbuminuria)",
    ],
    current_medications=[
        "Metformin 1000 mg BD",
        "Glipizide 5 mg OD",
        "Amlodipine 5 mg OD",
        "Atorvastatin 20 mg OD",
        "Losartan 50 mg OD",
    ],
    recent_reports=[
        "diabetes/diabetes__Ramesh_Kumar__52M.pdf",
        "metabolic_syndrome/metabolic_syndrome__Rajan_Pillai__60M.pdf",
        "ckd_early/ckd_early__Naresh_Babu__58M.pdf",
        "high_cholesterol/high_cholesterol__Kiran_Mehta__40M.pdf",
    ],
    demo_questions=[
        # Diabetes management
        "Is my diabetes well controlled? My HbA1c is 8.4%.",
        "What HbA1c target should I aim for given my age?",
        "My fasting blood sugar is 162 mg/dL — what does that mean?",
        # Kidney / multi-condition
        "My eGFR dropped from 64 to 58 over 3 months — should I be worried?",
        "Which of my medications are safe with early kidney disease?",
        # Cardio risk
        "My LDL is 178 mg/dL and I'm on a statin — is that acceptable?",
        "What is my overall cardiovascular risk?",
        # Lifestyle
        "I walk 4,000 steps a day — is that enough for a diabetic?",
        "What diet changes will help bring my triglycerides down?",
        # Summary
        "Summarise all my abnormal lab results in simple language.",
    ],
)

# ── Persona 3 — Dr. Arjun Mehta (Cardiologist) ───────────────────────────────

PERSONA_DR_MEHTA = DoctorPersona(
    id="demo-doctor-mehta-003",
    name="Dr. Arjun Mehta",
    specialization="Cardiology",
    hospital="Fortis Hospital, Bengaluru",
    years_experience=18,
    manages_patients=[
        PERSONA_MEERA.id,
        PERSONA_RAJAN.id,
    ],
    demo_questions=[
        # Clinical decision support
        "Which of my patients have active critical alerts right now?",
        "Show me Rajan's latest lipid panel and cardiac risk score.",
        "Has Meera's anaemia improved since she started iron supplements?",
        # Cross-patient view
        "List all patients with HbA1c above 8% in my panel.",
        "Which patients had lab results flagged in the last 7 days?",
        # Environment / population
        "Are any of my patients in cities with AQI > 150 today?",
        "Summarise Rajan's trend over the last month for my clinical notes.",
    ],
)

# ── Convenience exports ───────────────────────────────────────────────────────

ALL_PERSONAS = [PERSONA_MEERA, PERSONA_RAJAN, PERSONA_DR_MEHTA]

# Flat map of id → persona for quick lookup
PERSONA_BY_ID = {p.id: p for p in ALL_PERSONAS}

# Patient-only list (useful for seeding patient-scoped endpoints)
PATIENT_PERSONAS = [p for p in ALL_PERSONAS if p.role == "patient"]


if __name__ == "__main__":
    for persona in ALL_PERSONAS:
        role_tag = f"[{persona.role.upper()}]"
        name = persona.name  # type: ignore[union-attr]
        print(f"{role_tag} {name}  id={persona.id}")
        for q in persona.demo_questions[:3]:
            print(f"   • {q}")
        print()
