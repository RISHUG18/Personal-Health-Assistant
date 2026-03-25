#!/usr/bin/env bash
# Video Production Script
# Records screen flows for Mobile App and Doctor Dashboard
# Requires: ffmpeg, xdotool (Linux) or AppleScript (macOS)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="$SCRIPT_DIR/videos"
RECORDS_DIR="$OUTPUT_DIR/raw_recordings"
EDITS_DIR="$OUTPUT_DIR/edited"

mkdir -p "$RECORDS_DIR" "$EDITS_DIR"

echo "🎬 HealthAI Video Production Setup"
echo "==================================="
echo ""
echo "This script guides video recording of the Golden Path demonstration."
echo "Output will be saved to: $OUTPUT_DIR"
echo ""
echo "REQUIREMENTS:"
echo "  - ffmpeg (for screen recording and editing)"
echo "  - Two browser windows side-by-side: Mobile App + Doctor Dashboard"
echo "  - Audio recording device configured"
echo ""
echo "PREREQUISITES:"
echo "  1. Frontend running: http://localhost:3000"
echo "  2. Backend running: http://localhost:8000"  
echo "  3. Seeded with golden path data"
echo ""
read -p "Press Enter to continue..."

echo ""
echo "📋 SCRIPT OUTLINE (3-5 minutes)"
echo "=============================="
echo ""

# Save the script to a file
cat > "$OUTPUT_DIR/VIDEO_SCRIPT.md" << 'ENDSCRIPT'
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

ENDSCRIPT

echo "✅ Video script saved to: $OUTPUT_DIR/VIDEO_SCRIPT.md"

# Create filming checklist
cat > "$OUTPUT_DIR/filming_checklist.txt" << 'ENDCHECKLIST'
HealthAI Video Production Checklist
===================================

PRE-PRODUCTION
==============
[ ] Backend server running (port 8000)
[ ] Frontend server running (port 3000)  
[ ] Golden path data seeded in database
[ ] Test credentials prepared:
    - Patient: riya@example.com / PatientPass789!
    - Doctor: priya@hospital.local / SecurePass123!
[ ] Demo accounts logged in and ready
[ ] Audio recording device tested
[ ] Screen recording software configured
[ ] Display resolution set to 1920x1080
[ ] Zoom level set for visibility (100%)
[ ] Browser windows positioned (side-by-side if possible)
[ ] Internet connectivity verified
[ ] Mobile emulator / browser ready

FILMING
=======
Mobile App Flows (Scene 1-5)
[ ] Scene 1: Login screen recorded
[ ] Scene 2: Dashboard + alert banner recorded
[ ] Scene 3: Report timeline + lab values recorded
[ ] Scene 4: Environment panel recorded
[ ] Scene 5: Voice interaction recorded

Doctor Dashboard Flows (Scene 6-10)
[ ] Scene 6: Doctor login recorded
[ ] Scene 7: Patient priority list recorded
[ ] Scene 8: Patient detail view recorded
[ ] Scene 9: Alert details & evidence recorded
[ ] Scene 10: Doctor acknowledgement recorded

Scene 11: Summary
[ ] Summary montage recorded or will be created in post

AUDIO
=====
[ ] Narration script reviewed
[ ] Narration recorded in quiet environment
[ ] Audio levels normalized
[ ] Background music selected (royalty-free)
[ ] SFX (UI interactions, notifications) identified

POST-PRODUCTION
===============
[ ] Raw footage organized by scene
[ ] Color grading applied (consistent look)
[ ] Transitions added between scenes
[ ] Narration synced with footage
[ ] Background music layered
[ ] Lower thirds added (scene titles)
[ ] Captions generated (optional)
[ ] Final video exported at 1080p 30fps
[ ] File size optimized (<500MB target)
[ ] Quality check: Sound, video, timing
[ ] Final deliverable uploaded to GitHub

DELIVERY
========
[ ] `healthai_demo_final.mp4` uploaded to repo
[ ] `VIDEO_SCRIPT.md` included in docs
[ ] `filming_checklist.txt` saved
[ ] README updated with video link
[ ] GitHub commit with "Video: completed golden path demo"

ENDCHECKLIST

echo "✅ Filming checklist saved to: $OUTPUT_DIR/filming_checklist.txt"

echo ""
echo "📹 Recording Instructions:"
echo "=========================="
echo ""
echo "1. START RECORDING (using ffmpeg or screen recorder of choice)"
echo ""
echo "   # Option A: ffmpeg on Linux"
echo "   ffmpeg -f x11grab -s 1920x1080 -i :0 -f pulse -i default output.mp4"
echo ""
echo "   # Option B: macOS QuickTime"
echo "   QuickTime Player → File → New Screen Recording"
echo ""
echo "   # Option C: Windows (OBS Studio)"
echo "   Record with OBS at 1080p 30fps"
echo ""
echo "2. FOLLOW THE SCRIPT (in VIDEO_SCRIPT.md)"
echo ""
echo "3. SAVE RECORDINGS to: $RECORDS_DIR"
echo ""
echo "4. EDIT VIDEO:"
echo "   - Use ffmpeg, Adobe Premiere, or similar"
echo "   - Add narration, transitions, titles"
echo "   - Export to: $EDITS_DIR"
echo ""
echo "📄 Next Steps:"
echo "=============="
echo ""
echo "View script details: cat $OUTPUT_DIR/VIDEO_SCRIPT.md"
echo "View filming checklist: cat $OUTPUT_DIR/filming_checklist.txt"
echo ""
echo "✅ Setup complete!"