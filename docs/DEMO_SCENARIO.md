# Person 5 Demo Scenario — Release 1

## Goal

Show a safe, end-to-end demonstration of the HealthCompanion MVP using only synthetic data.

## Recommended demo path

### 1. Dashboard
- Open `/`
- Select **Meera Iyer**
- Point out the summary tiles, critical alert banner, and environment preview

### 2. Alerts
- Open `/alerts.html`
- Expand the haemoglobin alert
- Highlight the evidence values and the explanation drawer
- Acknowledge one alert to show interactive state changes

### 3. Reports
- Open `/reports.html`
- Show the uploaded PDF timeline
- Highlight extracted findings from the latest report
- Optionally click the upload zone to show the UI-only intake flow

### 4. Trends
- Open `/trends.html`
- Show steps, sleep, and heart rate trends for the past 7 days
- Explain the weekly insight notes and latest lab snapshot

### 5. AI Chat
- Open `/chat.html`
- Ask: `What does my latest haemoglobin reading mean?`
- Then ask: `Is today's AQI safe for an evening run?`
- Highlight citations and the non-diagnostic disclaimer

### 6. Doctor View
- Open `/doctor.html`
- Show the patient roster, cross-patient alert counts, and drill into Rajan Subramaniam
- Explain how doctor mode would use a more concise, evidence-focused prompt

### 7. Environment
- Open `/environment.html`
- Show AQI, PM2.5, temperature, humidity, and AQI scale reference
- Explain how environmental conditions can increase alert severity

## Demo personas

### Meera Iyer
- 28F, Chennai
- Iron deficiency anaemia, Vitamin D insufficiency
- Best demo questions:
  - What does my latest haemoglobin reading mean?
  - Is today's AQI safe for an evening run?
  - Summarise my report in simple language.

### Rajan Subramaniam
- 55M, Bengaluru
- Type 2 diabetes, hypertension, dyslipidaemia, early CKD
- Best demo questions:
  - Is my diabetes well controlled?
  - What is my cardiovascular risk?
  - My eGFR dropped — should I worry?

### Dr. Arjun Mehta
- Cardiologist
- Best demo questions:
  - Which patients need urgent review?
  - Show me Rajan's latest critical findings.
  - Has Meera's anaemia improved?

## QA checklist before demo

- [ ] `uvicorn backend.main:app --reload` starts successfully
- [ ] `/` loads the static dashboard
- [ ] `/docs` loads FastAPI docs
- [ ] `alerts.html`, `reports.html`, `trends.html`, `chat.html`, `doctor.html`, and `environment.html` all render
- [ ] Patient selector works on user-facing pages
- [ ] Alert expand / acknowledge / dismiss interactions work
- [ ] Chat suggested questions populate and responses render
- [ ] Sample reports exist under `src/sample_reports/`
- [ ] `src/backend/.env` contains real values if live integrations are required

## Notes

- This demo uses synthetic patient data only.
- The frontend falls back to demo data if backend endpoints are missing or unavailable.
- No diagnosis is shown; all AI messaging is framed as informational guidance.
