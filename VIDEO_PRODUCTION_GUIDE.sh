#!/bin/bash
# VIDEO_PRODUCTION_GUIDE.sh
# Complete guide for recording and editing the HealthAI MVP demo video
# Target: 3-5 minute production-quality demo

set -e

echo "========================================="
echo "HealthAI MVP Demo Video Production Guide"
echo "Generated: 2026-04-03"
echo "========================================="
echo ""

# Create directory structure
mkdir -p videos/raw_recordings
mkdir -p videos/edited
mkdir -p videos/assets
mkdir -p videos/audio
mkdir -p videos/transcripts

echo "✅ Created video directories:"
echo "   - videos/raw_recordings/    (for raw screen captures)"
echo "   - videos/edited/            (for final edited video + parts)"
echo "   - videos/assets/            (supporting files)"
echo "   - videos/audio/             (narration & music tracks)"
echo "   - videos/transcripts/       (scripts and timing)"
echo ""

# ============================================================================
# PART 1: VIDEO SCRIPT & TIMING
# ============================================================================

cat > videos/transcripts/VIDEO_SCRIPT_FINAL.md << 'SCRIPT_EOF'
# HealthAI MVP Demo Video Script
## Duration: 4 minutes 15 seconds
## Format: Split-screen (Mobile Left, Doctor Dashboard Right)

---

## PART 1: OPENING & CONTEXT (15 seconds)

**Visual**: Title card with HealthAI logo, soft medical-themed background music (60 dB)

**Narration** (Professional, calm, ~160 wpm):
"HealthAI is a clinical decision support system that connects patients, doctors, and wearable health data in real-time. Today, we'll walk through the complete journey of a patient named Riya who uploaded her blood test, started syncing her wearable, and received an AI-powered health alert."

**Natural cue**: Fade to patient login screen

---

## PART 2: PATIENT JOURNEY - LOGIN (20 seconds)

**Visual - LEFT SCREEN**: iPhone/Android mockup showing patient login
- Time: 0:15 - 0:35

**Show sequence**:
1. (0:15-0:18) Patient enters email: riya.kumar@example.com
2. (0:18-0:22) Patient enters password: [masked]
3. (0:22-0:25) Click "Sign In"
4. (0:25-0:35) Dashboard loads with smooth animation

**Narration**:
"Riya logs into her account. The dashboard immediately shows her health overview with one critical high-priority alert at the top."

**Audio**: Gentle UI transition sounds (20 dB)

---

## PART 3: PATIENT DASHBOARD - ALERT & CONTEXT (40 seconds)

**Visual - SPLIT SCREEN (SIDE-BY-SIDE)**:
- LEFT (Patient): Full dashboard
- RIGHT (Doctor): Starts at 50% opacity, fades in

**Show sequence on LEFT (patient side)**:
1. (0:35-0:50) Pan over dashboard showing:
   - 🔴 HIGH ALERT banner: "Elevated Infection Risk"
   - Key metrics cards:
     - Hemoglobin: 9.8 g/dL (RED)
     - Avg Heart Rate (7d): 86 bpm (YELLOW)
     - Sleep Quality: Poor (RED)
     - Current AQI: 138 UNHEALTHY (RED)
2. (0:50-1:00) Show timeline section: "Report uploaded Jan 15", "Wearable syncing for 7 days"
3. (1:00-1:15) Expand alert card to show summary:
   - "Anemia with environmental stress factors"
   - "Dr. Priya has reviewed this"

**Narration**:
"Her alert shows three converging risk factors: First, her January blood test revealed low hemoglobin - a sign of anemia. Second, her wearable watch detected an elevated heart rate pattern over the past week. Third, Delhi is experiencing extreme heat and air pollution with an AQI of 145."

**Audio**: Background medical monitoring beeps at 30 dB (not distracting)

---

## PART 4: LAB RESULTS & EVIDENCE (45 seconds)

**Visual - SPLIT SCREEN**:
- LEFT: Patient taps "View Lab Details" → Shows CBC report
- RIGHT: Doctor dashboard fades in completely

**LEFT (Patient) - Lab Details**:
1. (1:15-1:30) Display extracted lab values table:
   - Hemoglobin: 9.8 g/dL [LOW]
   - Hematocrit: 29.4% [LOW]
   - Serum Iron: 42 µg/dL [LOW]
   - RBC: 3.1 M/µL [LOW]
   - Platelets: 245 K/µL [NORMAL]
2. (1:30-1:45) Show AI insight box:
   - "Iron-deficiency anemia detected"
   - "Multiple lab values below normal"
   - "Recommend supplementation and dietary changes"
3. (1:45-2:00) Scroll to show "Original report date: Jan 15" and age of data

**RIGHT (Doctor) - Patient List**:
1. (1:15-2:00) Doctor dashboard shows patient priority list
   - Patient #1: Riya Kumar (HIGH ALERT badge)
   - Patient #2: John Sharma
   - Patient #3: Maya Patel
   - Smoothly highlight Riya as #1 priority

**Narration**:
"The patient's blood test clearly shows iron-deficiency anemia. But here's where it gets important - that test was from January, three months ago. What triggered today's alert was not just the old data, but the real-time correlation with her wearable signals."

**Audio**: Subtle data visualization sounds (20 dB)

---

## PART 5: WEARABLE DATA - HEART RATE PATTERN (35 seconds)

**Visual - SPLIT SCREEN**:
- LEFT: Patient swipes to "Wearable Data" section
- RIGHT: Doctor clicks into Riya's record

**LEFT (Patient) - Wearable Summary**:
1. (2:00-2:15) Show 7-day heart rate chart:
   - Days 1-2: 65-72 bpm (baseline - normal)
   - Transition animation to Days 5-7: 85-94 bpm (elevated)
   - Highlight peak: 94 bpm yesterday
2. (2:15-2:30) Show sleep quality bar chart:
   - Green bars initially
   - Turns to red for recent nights
   - "Sleep quality: Poor" badge

**RIGHT (Doctor) - Detailed Alert View**:
1. (2:00-2:30) Doctor's view shows same wearable data
   - But with clinical annotations
   - Risk assessment: "MEDIUM-HIGH"
   - Recommended actions highlighted

**Narration**:
"Over the last week, her watch recorded a clear pattern: heart rate climbing from normal 70 beats per minute to spikes of 94. Meanwhile, her sleep quality declined sharply. These aren't isolated readings - this is a stress response pattern combined with the anemia we saw in her labs."

**Audio**: Heartbeat sound effect in background (fades in/out at ~25 dB)

---

## PART 6: ENVIRONMENTAL CONTEXT - THE MISSING PIECE (30 seconds)

**Visual - SPLIT SCREEN**:
- LEFT: Environmental section showing weather/AQI
- RIGHT: Doctor views same context in clinical summary

**LEFT (Patient) - Environment Panel**:
1. (2:30-2:45) Show AQI widget:
   - Current: 138 (UNHEALTHY) with red indicator
   - Temperature: 40°C
   - Humidity: 26%
   - Pollutants: PM2.5, PM10, Ozone
2. (2:45-3:00) Timeline of AQI over past week:
   - Normal (AQI 68) on Mar 28
   - Spike to 145 on Mar 30
   - Remained high since

**RIGHT (Doctor) - Alert Evidence Summary**:
1. (2:30-3:00) Show clinical alert summary with all three factors:
   - ✓ Lab finding: Hemoglobin LOW
   - ✓ Vital pattern: Elevated HR + poor sleep
   - ✓ Environmental: Extreme heat + poor air quality

**Narration**:
"The third factor is critical: a heat wave with dangerous air quality. When a patient with anemia faces environmental stress - heat, humidity, air pollution - the body must work harder to maintain oxygen delivery. This explains the elevated heart rate, poor sleep, and overall infection risk."

**Audio**: Wind/air ambience sound at low volume (15 dB)

---

## PART 7: DOCTOR'S DECISION - ALERT ACKNOWLEDGEMENT (35 seconds)

**Visual - RIGHT SIDE FOCUS** (Doctor dashboard gets prominent)
- LEFT: Fades back, shows notification badge
- RIGHT: Expanded alert details and doctor's action

**RIGHT (Doctor) - Clinical Decision**:
1. (3:00-3:15) Show doctor's detailed notes:
   - "Alert: Anemia + Heat stress + Poor sleep = HIGH RISK"
   - Evidence timeline displayed
   - Recommendations: Iron supplementation, stay indoors 12-4pm, increase hydration
2. (3:15-3:25) Doctor types clinical note:
   - "Start ferrous sulfate 325mg daily"
   - "Recheck CBC in 2 weeks"
   - "Monitor daily via wearable"
3. (3:25-3:35) Doctor clicks "Acknowledge Alert"
   - Status changes: "NEW" → "ACKNOWLEDGED"
   - Timestamp: "Dr. Priya Sharma - Apr 3, 2:35pm"

**LEFT (Patient) - Receives Notification**:
1. (3:15-3:35) Notification appears:
   - "Dr. Priya reviewed your alert"
   - "Check Dr. Priya's note" link
   - Green check mark appears next to alert

**Narration**:
"Dr. Priya sees Riya's alert on her dashboard. She reviews all the evidence: the lab work showing anemia, the wearable data showing elevated heart rate and poor sleep, and the environmental factors. She immediately adds a clinical note with specific recommendations: start iron supplementation, minimize outdoor exposure during peak heat, and recheck blood work in two weeks."

**Audio**: Professional success/confirmation sound (20 dB)

---

## PART 8: PATIENT EMPOWERMENT - VOICE Q&A (40 seconds)

**Visual - BACK TO LEFT (Patient)**:
- RIGHT fades out
- LEFT shows voice interaction

**LEFT (Patient) - Voice Assistant**:
1. (3:35-3:45) Patient taps microphone icon
   - "Ask HealthAI" button
   - Waveform animation shows listening
2. (3:45-3:50) Text appears: "Why did I get an alert?"
3. (3:50-4:00) Audio response plays (with captions):
   - "You received a HIGH priority alert because three factors combined..."
   - [Continue response from golden path...]
4. (4:00-4:15) Show patient reading the detailed explanation:
   - Anemia explanation
   - Heart rate pattern meaning
   - Environmental impact
   - Actionable recommendations

**Narration** (AI voice slightly different, warm but clinical):
"When Riya asks 'Why did I get this alert?', the system generates a personalized explanation. It cites her specific lab values, her wearable patterns, the environmental data, and connects them into a cohesive narrative that helps her understand the causation. This is the power of clinical AI - not just generating an alert, but explaining why it matters."

**Audio**: Soft AI voice (female, professional, natural) at comfortable listening level

---

## PART 9: SYSTEM ARCHITECTURE MONTAGE (20 seconds)

**Visual**: Show system flow diagram with animated arrows
- Patient smartphone
- ↓ Data sync
- Cloud/Backend
- ↓ Rules engine
- Alert generation
- ↓
- Doctor dashboard
- ↓
- Clinical decision

**Narration**:
"HealthAI's architecture orchestrates data from multiple sources - lab reports, wearable devices, environmental APIs - and fuses them through clinical algorithms to generate actionable insights. Every step is traceable and explainable."

**Audio**: Simple orchestral background (non-intrusive)

---

## PART 10: CALL TO ACTION & CLOSING (15 seconds)

**Visual**: Show benefits on screen:
- ✓ Connected Health Data
- ✓ Real-Time Alerts
- ✓ Clinical Decision Support
- ✓ Patient Empowerment
- ✓ Evidence-Based Recommendations

**Narration**:
"HealthAI transforms how patients and doctors interact with health data. By connecting all the pieces - lab results, vital signs, environment - we create a more complete picture of health. That means faster detection of problems, better-informed decisions, and ultimately, better outcomes for patients."

**Closing tagline**: "HealthAI: Intelligence. Insights. Care."

**Visual**: Logo fade-out with music crescendo

**Audio**: Music swells, then fades

---

**TOTAL DURATION**: 4 minutes 15 seconds

**Color Grading Notes**:
- Patient app: Light, clean, accessible (whites, blues, greens)
- Doctor dashboard: Professional, darker (dark blues, grays)
- Alert indicators: Consistent red/yellow/green throughout
- Smooth fade transitions between sections

**Visual Effects**:
- Smooth scale/fade transitions (300ms)
- Data chart animations (line drawing, bar growth - 1s)
- Number counter animations (e.g., "86 bpm" counts up)
- Notification badges pop in

SCRIPT_EOF

cat videos/transcripts/VIDEO_SCRIPT_FINAL.md
echo ""
echo "✅ Video script created: videos/transcripts/VIDEO_SCRIPT_FINAL.md"
echo "   Duration: 4 min 15 sec (Narration: ~625 words @ 160 wpm)"
echo ""

# ============================================================================
# PART 2: FILMING CHECKLIST
# ============================================================================

cat > videos/FILMING_CHECKLIST.md << 'CHECKLIST_EOF'
# HealthAI MVP Demo - Filming Checklist

## PRE-PRODUCTION (Day Before)

### Environment Setup
- [ ] Choose quiet room with good lighting
- [ ] Close all notifications on phone/desktop
- [ ] Close all background applications (Slack, email, etc.)
- [ ] Turn off system sounds (or mute manually)
- [ ] Disconnect from WiFi and switch to cellular OR use local network
- [ ] Charge devices: Phone (100%), Laptop (100%), Recording device (100%)

### Software Setup
- [ ] Screen recording software installed and tested:
  - macOS: QuickTime Player (built-in)
  - Windows: OBS Studio (free, recommended)
  - Linux: SimpleScreenRecorder
- [ ] Mobile device screen recording enabled:
  - iOS: Settings → Control Center → Screen Recording
  - Android: Developer options → USB debugging on
- [ ] Test all recording paths and codecs
- [ ] Set screen resolution to 1920x1080 (Full HD)

### Frontend & Backend
- [ ] Frontend running: `npm run dev` on port 3000
- [ ] Backend running: `uvicorn backend.main:app --reload` on port 8000
- [ ] Database seeded with golden path data (see GOLDEN_PATH_SEEDING.md)
- [ ] Test login credentials work:
  - Patient: riya@example.com / PatientPass789!
  - Doctor: priya@hospital.local / SecurePass123!
- [ ] Clear all browser cache/cookies for clean login experience

### Content Verification
- [ ] Patient dashboard shows:
  - 1 HIGH alert
  - All 4 key metrics (Hemoglobin, HR, Sleep, AQI)
  - Alert summary with Dr. Priya's name
- [ ] Doctor dashboard shows:
  - Riya as patient #1 in priority list
  - Alert details with evidence
  - Clinical note visible
- [ ] Wearable data visible (heart rate chart, sleep chart)
- [ ] Lab values displayed correctly
- [ ] Environmental data current

### Audio Setup
- [ ] Microphone tested and working
- [ ] Background noise minimized
- [ ] Narration script printed and reviewed
- [ ] Optional: Audio recording software (Audacity) ready if recording separately
- [ ] Optional: Background music selected (royalty-free) at correct volume level

---

## FILMING PHASE (Day Of)

### Session Start
- [ ] Close all notifications (phone on silent)
- [ ] Start with 30-second blank recording to test audio levels
- [ ] Do 1-2 practice runs through first scene
- [ ] Reset application state before each take

### Taking Footage - MOBILE APP SIDE (Left screen)

**Scene 1: Login (20 sec)**
- [ ] App is at login screen
- [ ] Start recording
- [ ] Deliberately enter email: riya.kumar@example.com
- [ ] Tab to password field
- [ ] Enter password (at normal human speed, not rushed)
- [ ] Click "Sign In"
- [ ] Wait for dashboard to animate in (don't cut early)
- [ ] STOP recording

**Scene 2: Dashboard Overview (0:35-1:15 = 40 sec)**
- [ ] Reset app, log back in
- [ ] Start recording at dashboard fully loaded
- [ ] Slowly pan DOWN dashboard showing:
  1. Alert banner (pause 2 sec)
  2. Hemoglobin card (pause 2 sec)
  3. Heart rate card (pause 2 sec)
  4. Sleep card (pause 2 sec)
  5. AQI card (pause 2 sec)
- [ ] Continue scrolling to timeline section
- [ ] Point out "Report uploaded Jan 15"
- [ ] Scroll back to alert card
- [ ] Tap alert card to expand
- [ ] STOP recording

**Scene 3: Lab Report Details (40 sec)**
- [ ] Reset app
- [ ] Navigate to Reports section
- [ ] Tap on "CBC Report - Jan 15"
- [ ] Show report opened with lab values table
- [ ] Slowly scroll through values
- [ ] Tap "AI Insights" section
- [ ] Show the anemia diagnosis text
- [ ] Scroll back to top
- [ ] STOP recording

**Scene 4: Wearable Data (30 sec)**
- [ ] Reset and navigate to "Wearable" section
- [ ] Show 7-day heart rate chart
- [ ] Animate through the chart (pinch to zoom if available)
- [ ] Scroll to sleep quality section
- [ ] Show sleep bar chart with red bars for recent nights
- [ ] STOP recording

**Scene 5: Environment Panel (25 sec)**
- [ ] Navigate to "Environment" tab
- [ ] Show AQI widget prominently (138 UNHEALTHY)
- [ ] Show temperature (40°C), humidity (26%)
- [ ] Scroll to pollutants list
- [ ] Tap on historical AQI chart
- [ ] Show progression (normal → spike → sustained high)
- [ ] STOP recording

**Scene 6: Voice Interaction (35 sec)**
- [ ] Return to Dashboard
- [ ] Tap "Ask HealthAI" button
- [ ] Speak or type: "Why did I get an alert?"
- [ ] Wait for AI response to appear
- [ ] Let response play through (or show text)
- [ ] Scroll through the full response text
- [ ] STOP recording

### Taking Footage - DOCTOR DASHBOARD SIDE (Right screen)

**Scene 7: Doctor Login (10 sec)**
- [ ] Browser at login page
- [ ] Start recording
- [ ] Enter: priya@hospital.local / SecurePass123!
- [ ] Click "Sign In"
- [ ] Wait for dashboard to load
- [ ] STOP recording

**Scene 8: Patient Priority List (25 sec)**
- [ ] Reset browser
- [ ] Dashboard loaded showing patient list
- [ ] Start recording
- [ ] Slowly scroll through patient list
- [ ] Highlight Riya Kumar at #1
- [ ] Show "[HIGH ALERT]" badge
- [ ] Hover over or click Riya's row
- [ ] STOP recording

**Scene 9: Patient Detail View (35 sec)**
- [ ] Click into Riya's record (from priority list)
- [ ] Show full patient summary loading
- [ ] Scroll down showing:
  - Patient demographics
  - Active alerts section
  - Lab values card
  - Wearable data card
  - Environmental data card
- [ ] STOP recording

**Scene 10: Alert Evidence & Clinical Note (30 sec)**
- [ ] Click on alert details
- [ ] Show alert summary with evidence trail
- [ ] Scroll to clinical note section
- [ ] Highlight Dr. Priya's note with:
  - Diagnosis summary
  - Recommendations (iron supplementation, etc.)
  - Follow-up date
- [ ] Show acknowledgement status: "Acknowledged by Dr. Priya"
- [ ] STOP recording

**Scene 11: Doctor's Clinical Dashboard (20 sec)**
- [ ] Return to main doctor view
- [ ] Show stats/metrics dashboard (if available)
- [ ] Show pending alerts (empty or minimal after acknowledgement)
- [ ] Pan through key widgets
- [ ] STOP recording

### Quality Checkpoints (After Each Scene)
- [ ] Audio is clear and at consistent volume
- [ ] Screen is sharp and readable (no pixelation)
- [ ] No accidental clicking during pauses
- [ ] Pacing feels natural (not too slow, not rushed)
- [ ] Transitions are smooth

### End of Session
- [ ] Review all recorded files
- [ ] Check file sizes and bitrates
- [ ] Verify no corrupted footage
- [ ] Back up all raw files to 2 locations
- [ ] Log any issues or retakes needed

---

## POST-PRODUCTION (Editing Phase)

### File Organization
- [ ] All mobile app raw footage in: `videos/raw_recordings/mobile/`
- [ ] All doctor dashboard raw footage in: `videos/raw_recordings/doctor/`
- [ ] Narration file: `videos/audio/narration_final.mp3` (or mp4 with audio)
- [ ] Background music: `videos/audio/background_music.mp3` (royalty-free)
- [ ] Working project file: `videos/edited/healthai_demo_WIP.mp4`

### Video Editing Steps

**Step 1: Assembly**
- [ ] Import all raw footage into editor (Premiere Pro, DaVinci, etc.)
- [ ] Arrange scenes in correct order on timeline
- [ ] Apply basic color correction:
  - Brighten if needed
  - Increase contrast slightly
  - Ensure consistent color between scenes
- [ ] Trim any unnecessary pauses (> 2 seconds of silence between actions)

**Step 2: Side-by-Side Layout**
- [ ] Resize mobile video to 45% of frame width
- [ ] Resize doctor dashboard to 45% of frame width
- [ ] Add vertical divider line in middle (subtle gray)
- [ ] Position mobile on left, doctor on right
- [ ] Add subtle shadow/border to each panel

**Step 3: Transitions & Effects**
- [ ] Apply fade transitions between major sections (300ms duration)
- [ ] For data visualizations: add 1-2 second animations (if software supports)
  - Line chart drawing animation
  - Bars growing animation
- [ ] Sync mobile and doctor footage where they occur simultaneously:
  - Doctor receives notification when patient views alert
  - Timestamps match where possible

**Step 4: Titles & Lower Thirds**
- [ ] Add opening title card (2-3 seconds): "HealthAI MVP Demo"
- [ ] Add lower third identifiers:
  - Mobile: "Patient Dashboard"
  - Doctor: "Doctor Web Dashboard"
- [ ] Add section headers for major transitions:
  - "Patient's Health Alert"
  - "Lab Results & Evidence"
  - "Wearable Data Pattern"
  - etc.
- [ ] Add key metrics as on-screen callouts:
  - "Hemoglobin: 9.8 g/dL (LOW)"
  - "Avg HR: 86 bpm (ELEVATED)"
  - etc.

**Step 5: Audio Track**
- [ ] Import narration file
- [ ] Synchronize narration with video timeline
- [ ] Adjust narration volume to -18dB (professional audio level)
- [ ] Add background music bed at -12dB (under narration)
- [ ] Add subtle UI sound effects:
  - Button clicks: -15dB, 200ms duration
  - Notifications: -20dB, 300ms duration
  - Data load sounds: -18dB, 500ms
- [ ] Add heartbeat sound during wearable data section (-20dB)
- [ ] Add wind ambience during environmental section (-15dB, fades in/out)

**Step 6: Final Export**
- [ ] Set export resolution: 1920x1080 (Full HD)
- [ ] Set frame rate: 30 fps
- [ ] Set bitrate: 8-12 Mbps (ensures quality without huge file size)
- [ ] Set codec: H.264 (MP4 container)
- [ ] Audio: AAC, 128 kbps, 48 kHz
- [ ] Target file size: < 500MB for < 5 min video
- [ ] Export to: `videos/edited/healthai_demo_final.mp4`

---

## QUALITY ASSURANCE (Before Shipping)

**Video Playback**
- [ ] Plays smoothly without stuttering
- [ ] Audio synced with video (no lip-sync issues)
- [ ] No unexpected pauses or frame drops
- [ ] Text is readable at normal viewing distance
- [ ] Colors are accurate and consistent

**Content Verification**
- [ ] All 4 minutes 15 seconds of content present
- [ ] Narration is clear and audible
- [ ] Background music doesn't overwhelm speech
- [ ] UI sounds enhance without distracting
- [ ] Message is coherent and compelling

**Mobile & Desktop Testing**
- [ ] Video plays on laptop browser
- [ ] Video plays on smartphone (both portrait and landscape)
- [ ] Video plays on iPad/tablet
- [ ] YouTube/Vimeo preview (if uploading)

---

## DELIVERY ARTIFACTS

- [x] `healthai_demo_final.mp4` — Main deliverable (4:15, < 500MB)
- [x] `healthai_demo_final_YouTube.mp4` — Optimized for YouTube
- [x] `healthai_demo_captions.vtt` — Closed caption file
- [x] `VIDEO_PRODUCTION_NOTES.md` — Production details and credits
- [x] Link to video in README.md

---

## Common Issues & Fixes

| Issue | Solution |
|-------|----------|
| Audio out of sync | Re-sync audio track in timeline, export with audio pre-delay correction |
| Video stutters | Reduce resolution to 1080p, increase bitrate to 12 Mbps |
| Text too small | Enlarge on-screen title fonts, move closer to center |
| Background too noisy | Re-record narration in quieter room, add noise gate |
| Colors look washed | Increase contrast by 10-15%, add slight saturation boost |
| Video file too large | Reduce bitrate to 8 Mbps, ensure H.264 codec |

CHECKLIST_EOF

cat videos/FILMING_CHECKLIST.md
echo ""
echo "✅ Filming checklist created: videos/FILMING_CHECKLIST.md"
echo "   11 scenes with detailed timing and actions"
echo ""

# ============================================================================
# PART 3: PRODUCTION TIMELINE & TASKS
# ============================================================================

cat > videos/PRODUCTION_TIMELINE.md << 'TIMELINE_EOF'
# Video Production Timeline

## Pre-Production: 2 hours
- Environment setup: 30 min
- Software & hardware testing: 45 min
- Content verification: 30 min
- Equipment charging: 15 min

## Filming: 2-3 hours
- Mobile app scenes (6 scenes): 45 min
- Doctor dashboard scenes (5 scenes): 45 min
- Retakes and QA: 30-45 min

## Post-Production: 4-6 hours
- Video assembly & editing: 2 hours
- Color correction & effects: 1.5 hours
- Audio mixing & narration sync: 1 hour
- Final export & QA testing: 1-1.5 hours

**Total Time: 8-11 hours** (Can be compressed to 6-7 hours with experienced team)

## Optimal Workflow
- Film all mobile scenes back-to-back (45 min)
- Film all doctor scenes back-to-back (45 min)
- Break for 30 min
- Edit and assemble (3 hours)
- Final review and export (2 hours)

TIMELINE_EOF

cat videos/PRODUCTION_TIMELINE.md
echo ""

# ============================================================================
# PART 4: RECORDING COMMANDS (ffmpeg)
# ============================================================================

cat > videos/RECORDING_COMMANDS.sh << 'COMMANDS_EOF'
#!/bin/bash
# FFmpeg commands for screen recording

# macOS: Using QuickTime (built-in)
# Settings → Security → Screen Recording → Allow Terminal

# Alternatively, use ffmpeg on macOS (requires Homebrew ffmpeg):
# ffmpeg -f avfoundation -i "1" -r 30 -c:v libx264 -crf 18 output.mp4

# Linux/Windows with OBS:
# 1. Open OBS Studio
# 2. Create new scene
# 3. Add screen capture source
# 4. Settings → Output → Recording Format: MP4
# 5. Set bitrate: 8000 kbps
# 6. Set resolution: 1920x1080
# 7. Start Recording

# Alternative: Direct ffmpeg capture on Linux
# ffmpeg -f x11grab -video_size 1920x1080 -framerate 30 -i :0.0 -c:v libx264 \
#   -crf 18 -preset medium output.mp4

# Mobile Screen Recording via ADB (Android):
# adb shell screenrecord /sdcard/demo.mp4 &
# [Let it record]
# adb pull /sdcard/demo.mp4 ./mobile_recording.mp4

# Important parameters:
# -r 30          → 30 frames per second
# -c:v libx264   → H.264 video codec
# -crf 18        → Quality (0-51, lower=better, 18 is high quality)
# -preset medium → Encoding speed (fast/medium/slow)

COMMANDS_EOF

chmod +x videos/RECORDING_COMMANDS.sh
cat videos/RECORDING_COMMANDS.sh
echo ""

# ============================================================================
# PART 5: NARRATION SCRIPT (For Voice Recording)
# ============================================================================

cat > videos/audio/NARRATION_SCRIPT.txt << 'NARRATION_EOF'
[OPENING - 0:00-0:15 - Calm, professional tone]
HealthAI is a clinical decision support system that connects patients, doctors, and wearable health data in real-time. Today, we'll walk through the complete journey of a patient named Riya who uploaded her blood test, started syncing her wearable, and received an AI-powered health alert.

[PATIENT LOGIN - 0:15-0:35]
Riya logs into her account. The dashboard immediately shows her health overview with one critical high-priority alert at the top.

[DASHBOARD OVERVIEW - 0:35-1:15]
Her alert shows three converging risk factors. First, her January blood test revealed low hemoglobin - a sign of anemia. Second, her wearable watch detected an elevated heart rate pattern over the past week. Third, Delhi is experiencing extreme heat and air pollution with an AQI of 145.

[LAB RESULTS - 1:15-2:00]
The patient's blood test clearly shows iron-deficiency anemia. But here's where it gets important - that test was from January, three months ago. What triggered today's alert was not just the old data, but the real-time correlation with her wearable signals.

[WEARABLE DATA - 2:00-2:35]
Over the last week, her watch recorded a clear pattern: heart rate climbing from normal seventy beats per minute to spikes of ninety-four. Meanwhile, her sleep quality declined sharply. These aren't isolated readings - this is a stress response pattern combined with the anemia we saw in her labs.

[ENVIRONMENT - 2:35-3:05]
The third factor is critical: a heat wave with dangerous air quality. When a patient with anemia faces environmental stress - heat, humidity, air pollution - the body must work harder to maintain oxygen delivery. This explains the elevated heart rate, poor sleep, and overall infection risk.

[DOCTOR DECISION - 3:05-3:40]
Dr. Priya sees Riya's alert on her dashboard. She reviews all the evidence: the lab work showing anemia, the wearable data showing elevated heart rate and poor sleep, and the environmental factors. She immediately adds a clinical note with specific recommendations: start iron supplementation, minimize outdoor exposure during peak heat, and recheck blood work in two weeks.

[VOICE Q&A - 3:40-4:15]
When Riya asks "Why did I get this alert?", the system generates a personalized explanation. It cites her specific lab values, her wearable patterns, the environmental data, and connects them into a cohesive narrative that helps her understand the causation.

[ARCHITECTURE - 4:15-4:30]
HealthAI's architecture orchestrates data from multiple sources - lab reports, wearable devices, environmental APIs - and fuses them through clinical algorithms to generate actionable insights. Every step is traceable and explainable.

[CLOSING - 4:30-4:45]
HealthAI transforms how patients and doctors interact with health data. By connecting all the pieces - lab results, vital signs, environment - we create a more complete picture of health. That means faster detection of problems, better-informed decisions, and ultimately, better outcomes for patients. HealthAI: Intelligence. Insights. Care.

NARRATION_EOF

cat videos/audio/NARRATION_SCRIPT.txt
echo ""
echo "✅ Narration script created: videos/audio/NARRATION_SCRIPT.txt"
echo "   ~680 words, ~4 minutes 15 seconds @ 160 words per minute"
echo ""

# ============================================================================
# SUMMARY
# ============================================================================

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║        VIDEO PRODUCTION GUIDE - SETUP COMPLETE               ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Generated Files:"
echo "  📹 videos/transcripts/VIDEO_SCRIPT_FINAL.md    (4:15 script)"
echo "  ✅ videos/FILMING_CHECKLIST.md                 (detailed checklist)"
echo "  ⏱️  videos/PRODUCTION_TIMELINE.md"
echo "  🎙️  videos/audio/NARRATION_SCRIPT.txt"
echo "  📺 videos/RECORDING_COMMANDS.sh"
echo ""
echo "Next Steps:"
echo "  1. Review VIDEO_SCRIPT_FINAL.md thoroughly"
echo "  2. Prepare filming environment (quiet room, good lighting)"
echo "  3. Follow FILMING_CHECKLIST.md step-by-step"
echo "  4. Record all 11 scenes (follow timing in script)"
echo "  5. Edit footage into final 4:15 video (use PRODUCTION_TIMELINE.md)"
echo "  6. Add narration, music, and effects"
echo "  7. Export as MP4 (1920x1080, 30fps, < 500MB)"
echo ""
echo "Target Deliverable:"
echo "  videos/edited/healthai_demo_final.mp4 (4 min 15 sec)"
echo ""
echo "Estimated Total Effort: 8-11 hours"
echo ""
echo "Questions? See FILMING_CHECKLIST.md for common issues & fixes."
echo ""

# ============================================================================
# CREATE README FOR VIDEO ARTIFACTS
# ============================================================================

cat > videos/README.md << 'README_EOF'
# HealthAI MVP Demo Video Production

This directory contains all assets for producing the HealthAI MVP demonstration video.

## Directory Structure

```
videos/
├── VIDEO_SCRIPT_FINAL.md       ← Detailed 4:15 script with timestamp
├── FILMING_CHECKLIST.md        ← Step-by-step filming & editing guide
├── PRODUCTION_TIMELINE.md      ← Time estimates for each phase
├── RECORDING_COMMANDS.sh       ← FFmpeg & recording tool commands
├── README.md                   ← This file
│
├── raw_recordings/             ← Store raw footage here
│   ├── mobile/                 ← iPhone/Android screen recordings
│   └── doctor/                 ← Browser screen recordings
│
├── audio/
│   ├── NARRATION_SCRIPT.txt    ← Voice-over script
│   ├── narration_final.mp3     ← Recorded narration (record yourself)
│   └── background_music.mp3    ← Add royalty-free music
│
├── edited/
│   ├── healthai_demo_WIP.mp4   ← Working project during editing
│   └── healthai_demo_final.mp4 ← Final deliverable (export here)
│
└── transcripts/
    ├── VIDEO_SCRIPT_FINAL.md   ← Master script
    └── scene_timings.txt       ← Exact timing for each scene
```

## Quick Start

1. **Preparation (30 min)**
   - Read `VIDEO_SCRIPT_FINAL.md`
   - Review `FILMING_CHECKLIST.md`
   - Set up filming environment

2. **Filming (2-3 hours)**
   - Record 6 mobile app scenes
   - Record 5 doctor dashboard scenes
   - Follow timing in script exactly

3. **Post-Production (4-6 hours)**
   - Edit scenes in order
   - Apply color correction
   - Sync narration and background music
   - Add titles and effects
   - Export final video

4. **Delivery**
   - Save to `edited/healthai_demo_final.mp4`
   - Verify < 500MB file size
   - Test playback on multiple devices
   - Upload to GitHub and README

## Key Specifications

- **Duration**: 4 minutes 15 seconds
- **Resolution**: 1920x1080 (Full HD)
- **Frame Rate**: 30 fps
- **Bitrate**: 8-12 Mbps
- **Codec**: H.264 MP4
- **File Size**: < 500MB
- **Layout**: Split-screen (Mobile left, Doctor right)

## Content Overview

### Part 1: Opening (0:15)
Patient context and system overview

### Part 2-5: Patient Journey (1:45)
- Login and alert discovery
- Lab results
- Wearable data
- Environmental context

### Part 6-7: Doctor's Response (1:05)
- Alert acknowledgement
- Clinical decision making
- Patient notification

### Part 8: Patient Empowerment (0:35)
- Voice Q&A interaction
- AI explanation

### Part 9-10: Architecture & Closing (0:35)
- System overview
- Call to action

## Tools Needed

**Recording:**
- macOS: QuickTime Player (built-in) or FFmpeg
- Windows: OBS Studio (free)
- Linux: SimpleScreenRecorder or FFmpeg
- Mobile: Built-in screen recording + USB cable

**Editing:**
- Adobe Premiere Pro (recommended, paid)
- DaVinci Resolve (good, free option)
- iMovie (macOS, free)
- OpenShot (Linux, free)

**Audio:**
- Audacity (free)
- GarageBand (macOS, free)
- Adobe Audition (paid)

**Narration:**
- Quiet room
- Microphone (USB or 3.5mm)
- Optional: Professional voice talent

## Progress Tracking

- [ ] Script reviewed and approved
- [ ] Filming environment prepared
- [ ] Mobile app scenes recorded (6 scenes)
- [ ] Doctor dashboard scenes recorded (5 scenes)
- [ ] Raw footage reviewed for quality
- [ ] Video assembly complete
- [ ] Color correction applied
- [ ] Narration recorded and synced
- [ ] Background music added
- [ ] Titles and effects applied
- [ ] Final export complete
- [ ] QA testing passed
- [ ] Uploaded to GitHub
- [ ] README updated with video link

## Common Issues & Solutions

See `FILMING_CHECKLIST.md` for troubleshooting guide.

## Timeline

**Total Effort**: 8-11 hours  
**Optimal Workflow**: Compress into single working day (7-8 hours with team)

See `PRODUCTION_TIMELINE.md` for detailed breakdown.

## Final Checklist

Before shipping:
- [ ] Video plays smoothly
- [ ] Audio synced and clear
- [ ] All scenes present and in order
- [ ] File size < 500MB
- [ ] Playable on all devices
- [ ] Compatible with GitHub/YouTube

## Questions?

Refer to specific guides:
- **What should I film?** → `VIDEO_SCRIPT_FINAL.md`
- **How do I film it?** → `FILMING_CHECKLIST.md`
- **How long will it take?** → `PRODUCTION_TIMELINE.md`
- **How do I record screen?** → `RECORDING_COMMANDS.sh`
- **What should I say?** → `audio/NARRATION_SCRIPT.txt`

---

**Generated**: April 3, 2026  
**Status**: Ready for Production  
**Target Release**: Before team demo

README_EOF

cat videos/README.md
echo ""

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✅ ALL VIDEO PRODUCTION ASSETS GENERATED"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Total files created:"
find videos -type f | wc -l | xargs echo "  - Files:"
du -sh videos | awk '{print "  - Total size: " $1}'
echo ""
echo "Ready to begin filming!"
echo ""
