## 1. Medical Reports Schema

Medical reports must include:

- User ownership identifier
- Source file metadata
- Immutable full OCR text
- OCR provenance information
- Creation timestamp

Medical reports represent the **single source of truth** for uploaded documents.
OCR text stored here must remain **unaltered and immutable**.

Medical reports cannot be deleted without cascading removal of derived data.

---

## 2. Lab Results Schema

Lab results must include:

- Reference to a medical report
- Test name
- Numeric value (if extractable)
- Measurement unit
- Reference range (as reported)
- Optional abnormal flag
- Source page number

Each lab result represents **one atomic, independently verifiable fact**.
No medical interpretation or diagnosis is stored at this level.

Lab results may exist only if they can be mechanically extracted with confidence.
If extraction is uncertain, data remains in OCR text only.

---

## 3. Alerts Schema

Alerts must include:

- User identifier
- Severity level (`low`, `medium`, `high`)
- Human-readable reason
- Creation timestamp

Alerts represent **deterministic system signals**, not medical diagnoses.
Severity indicates **operational urgency**, not clinical judgment.

Alerts cannot exist without corresponding evidence.

---

## 4. Alert Evidence Schema

Alert evidence must include:

- Reference to an alert
- Reference to a medical report and/or lab result
- Optional verbatim OCR text snippet

Alert evidence provides **explicit justification** for alert creation.
Every alert must be fully explainable using stored evidence alone.

Evidence must be:
- Verifiable
- Traceable
- Stored (not generated dynamically)

LLM-generated or inferred evidence is not permitted.

---

## 5. RAG Metadata Contract

Every retrieved or embedded chunk must include:

- `user_id`
- `report_id`
- `section`
- `report_date`
- `embedding_model`
- `embedding_version`

RAG metadata ensures:
- User data isolation
- Source traceability
- Temporal reasoning
- Embedding reproducibility

Chunks missing required metadata must be rejected and not embedded.

---

## 6. Design Constraints and Guarantees

The schema design guarantees:

- Full auditability of system behavior
- Explicit linkage between alerts and source evidence
- Safe interaction with downstream LLMs
- Prevention of hallucinated or untraceable outputs

All intelligence layers operate **on top of** these schemas and must conform to them.
Schemas are considered authoritative and immutable once deployed.
