# HealthAI Demo Video Script (3-5 minutes)

## Part 1: Patient Journey (Mobile App) - 1:30 min

### Scene 1: Patient Registration
- **Visual**: Mobile app login screen
- **Action**: 
  - Patient (Riya) enters credentials
  - Taps "Login"
- **Narration**: "Riya Sharma is a 28-year-old with recent health concerns. She logs into the HealthAI app to access her health summary and get personalized insights."
- **Duration**: 15 seconds

### Scene 2: Dashboard Overview
- **Visual**: Dashboard with health metrics, active alerts banner
- **Action**: 
  - Show: Alert banner "High AQI + Anaemia Risk"
  - Scroll to see: Heart rate chart, sleep metrics
- **Narration**: "Her dashboard immediately shows an active health alert: High AQI combined with her anaemia puts her at infection risk. Her recent wearable data (low sleep, elevated heart rate) is contributing factors."
- **Duration**: 30 seconds

### Scene 3: Reports Timeline  
- **Visual**: Reports page with chronological list
- **Action**:
  - Tap: CBC Report (Jan 2026)
  - Expand: Shows extracted values
    - Hemoglobin: 9.8 g/dL (LOW)
    - Serum Iron: 42 µg/dL (LOW)
- **Narration**: "Riya uploaded a blood test from January showing low hemoglobin and iron levels—signs of anaemia. The system extracted these key values automatically."
- **Duration**: 25 seconds

### Scene 4: Environment Context
- **Visual**: Environment panel
- **Action**:
  - Show: AQI gauge (145 - Unhealthy)
  - Show: Temperature (35°C - Heatwave)
  - Show: Humidity
- **Narration**: "Combined with Chennai's current heatwave (35°C) and poor air quality (AQI 145), these factors increase her risk."
- **Duration**: 20 seconds

### Scene 5: Voice Interaction
- **Visual**: Chat interface
- **Action**:
  - Tap: Microphone icon
  - Say (or show text): "Why did I get an alert?"
  - Show: AI response appearing in chat
- **Narration**: "Riya asks the AI assistant why she got the alert. The app retrieves her lab values, environment data, and wearable metrics to provide a personalized explanation."
- **AI Response**: "You got an alert because your blood test shows low hemoglobin (9.8 g/dL), indicating anaemia. Combined with Chennai's high air quality index (145) and your recent sleep of 5.8 hours, this increases your infection risk."
- **Duration**: 30 seconds

---

## Part 2: Doctor Dashboard Review - 1:30 min

### Scene 6: Doctor Login
- **Visual**: Doctor dashboard login
- **Action**:
  - Enter Doctor credentials
  - Tap "Login"
- **Narration**: "Meanwhile, Dr. Priya Nair, Riya's assigned physician, logs into the HealthAI doctor dashboard."
- **Duration**: 10 seconds

### Scene 7: Patient Priority List
- **Visual**: Doctor dashboard showing patient roster
- **Action**:
  - Show: Ranked list of patients
  - Highlight: Riya at top (3 active alerts)
  - Tap: Riya's entry
- **Narration**: "The doctor dashboard automatically prioritizes patients based on alert severity. Riya appears at the top with 3 active alerts requiring attention."
- **Duration**: 25 seconds

### Scene 8: Patient Detail View
- **Visual**: Detailed patient summary
- **Action**:
  - Show: Patient demographics
  - Show: Alert timeline (High, Medium, Low)
  - Show: Recent reports
  - Show: Wearable metrics (heart rate graph, sleep chart)
  - Show: Environment data
- **Narration**: "Drilling into Riya's record, Dr. Priya can see: her lab values with automatic interpretation, a timeline of all health alerts, 7-day wearable trends, and real-time environmental context."
- **Duration**: 35 seconds

### Scene 9: Alert Details & Evidence
- **Visual**: Expanded alert card
- **Action**:
  - Show: "High AQI + Anaemia Risk" alert
  - Show: Evidence drawer (CBC results, AQI, sleep metrics)
  - Show: AI-generated summary with confidence score
- **Narration**: "Each alert shows its evidence: the specific lab values and environmental factors that triggered it. This helps the doctor quickly understand the clinical reasoning."
- **Duration**: 20 seconds

### Scene 10: Doctor Response
- **Visual**: Doctor acknowledgment and note-adding
- **Action**:
  - Tap: Acknowledge alert
  - Type: "Recommend iron supplements + limit heat exposure + follow-up CBC in 4 weeks"
  - Tap: Save
- **Narration**: "Dr. Priya acknowledges the alert and adds a clinical recommendation directly in the system. Riya will see this guidance on her mobile app."
- **Duration**: 20 seconds

---

## Part 3: System Flow Summary - 30 seconds

### Scene 11: Summary Animation
- **Visual**: Split screen or montage of both interfaces
- **Narration**: "The HealthAI system enables seamless collaboration: Patients upload reports and sync wearable data. The system intelligently correlates this information to surface actionable insights. Doctors can instantly access prioritized cases and provide evidence-based guidance. And patients get clear, personalized explanations via AI-powered voice interaction."
- **Duration**: 30 seconds

---

## Technical Notes

### Mobile App Flows
- Mock login uses test credentials (auto-populated)
- Dashboard loads demo data from `mock_patient_detail.json`
- All API calls use mock responses or stub services
- No real backend connectivity required for demo

### Doctor Dashboard Flows
- Mock login with test credentials
- Patient list renders from `mock_doctor_roster.json`
- Detail view composes data from multiple mock sources
- Acknowledgement and notes update demo data state (no persistence needed)

### Audio/Narration
- Professional narration with clear, medical but accessible language
- Pacing: 150-160 words per minute (Standard speaking rate)
- Emphasis on the end-user value, not technical jargon

### Video Format
- Resolution: 1920x1080 (Full HD)
- Frame rate: 30 fps
- Duration: 3-5 minutes total
- Captions: Optional (best practice)

---

## Deliverables

1. **Raw Recordings**
   - `mobile_app_flow.mp4` (1:30 min)
   - `doctor_dashboard_flow.mp4` (1:30 min)

2. **Edited Video**
   - `healthai_demo_final.mp4` (3-5 min, split-screen or sequential)

3. **Supporting Assets**
   - `VIDEO_SCRIPT.md` (This file)
   - `filming_checklist.txt`
   - Narration audio track

