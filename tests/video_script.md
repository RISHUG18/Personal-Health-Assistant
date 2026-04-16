# DASS Health MVP - Video Production Narration & Checklist

**Total Video Duration:** 3-5 minutes  
**Narration:** ~2.5-3.5 minutes (remainder is silent screen demo)

---

## SUBMISSION REQUIREMENTS ✓

This runbook satisfies ALL video production requirements:

✅ **3-5 Minute Script**: Complete word-for-word narration with timings (scenes, narration, editing notes)

✅ **Smooth Screen Flows**: Step-by-step recording checklist with dry runs, smooth transitions, no jumps

✅ **Mobile App + Web Dashboard Side-by-Side / Alternating**: 
   - See "EDITING CHECKLIST" → "Key Feature: Side-by-Side / Alternating Mobile App & Web Dashboard"
   - Option A: Split screen (Patient app left 50%, Doctor dashboard right 50%)
   - Option B: Alternating cuts (20-30 sec patient view, cross-dissolve, 20-30 sec doctor view, repeat)
   - Technical instructions provided for DaVinci Resolve implementation

---

## VIDEO NARRATION - WORD-FOR-WORD SCRIPT

**[Read this in a calm, enthusiastic, professional tone]**

---

### INTRO NARRATION (30 seconds)
*[Start as title card appears with DASS Health logo]*

"Introducing DASS Health: An AI-powered healthcare platform that transforms 
how patients, doctors, and wearable data collaborate to create actionable 
health insights.

Today, we'll follow Alex, a patient whose uploaded lab work and Apple Watch 
data revealed a critical health pattern. We'll see how the system alerts both 
patient and doctor, synthesizes clinical insights, and empowers evidence-based 
decision-making.

Let's get started."

---

### SCENE 2-3: PATIENT DASHBOARD (50 seconds)
*[Patient login visible on screen]*

"Alex logs into their patient portal. The dashboard immediately displays two 
key pieces of health information:

First, recent medical reports. Alex uploaded a comprehensive blood test 30 
days ago that revealed elevated cholesterol levels. The system has extracted 
and highlighted the key findings:

Total Cholesterol: 245 mg/dL — that's high, above the recommended 200.
LDL cholesterol: 165 — the 'bad' cholesterol, should be below 100.
Triglycerides: 185 — also elevated, should be below 150.

Second, wearable data. Alex's Apple Watch has been syncing continuously over 
the past two weeks, capturing heart rate, steps, and sleep patterns.

Notice how the system doesn't overwhelm Alex with raw numbers. Instead, it 
highlights what matters: abnormal values are clearly flagged, and context is 
provided."

---

### SCENE 4: HEALTH ALERT (40 seconds)
*[Alert notification appears on patient screen]*

"Three days after uploading the blood test, the DASS Health AI system 
detected a pattern.

Elevated cholesterol combined with consistently elevated resting heart rate 
on the wearable device. The system generated a medium-priority alert and 
notified both Alex and their doctor, Dr. Sarah Mitchell.

The alert isn't just a generic warning. It explains the evidence:
'Your blood test shows high cholesterol and triglycerides. Combined with 
sustained elevated heart rate from your wearable, this pattern suggests 
cardiovascular stress.'

This is intelligence, not just data."

---

### SCENE 5: DOCTOR DASHBOARD (60 seconds)
*[Doctor login and patient summary visible]*

"Now let's look at the other side of the equation: the doctor's dashboard.

Dr. Mitchell logs in and immediately sees their patient roster. Alex's card 
is highlighted with a new alert flag.

Clicking on Alex's name brings up a comprehensive patient summary:

- Basic info: name, age, gender, contact method
- Medical history at a glance
- The recent blood test with all results clearly displayed
  - Abnormal values are marked in red
  - Charts show the lipid panel visually
- The wearable heart rate trend over 14 days, showing the elevation
- The multi-metric alert that triggered
- Dr. Mitchell's own clinical notes: 'Patient shows cardiovascular risk factors. 
  Referred for cardiologist evaluation. Recommended lifestyle modifications: 
  increased aerobic activity, dietary changes. Follow-up lipid panel in 6 weeks. 
  Consider statin therapy if lifestyle measures insufficient.'

All the information a clinician needs for informed decision-making, 
synthesized into one view."

---

### SCENE 6: PATIENT AI CHAT (80 seconds)
*[Patient opens chat interface and types question]*

"Here's where DASS Health becomes truly powerful: patient empowerment through 
AI-powered explanation.

Alex now asks the AI: 'Why did I get an alert? My doctor said there's some 
concern about my heart rate?'

The system doesn't just give a generic answer. It retrieves Alex's actual 
medical data, references their lab work, and generates a personalized 
explanation with sources:

'Your alert was generated because your recent health data shows a concerning 
pattern:

One: Your January 10th blood test showed elevated cholesterol. Total 
cholesterol was 245 mg/dL — that's 45 points above the recommended maximum 
of 200. Your LDL, the harmful form of cholesterol, was 165 — that's 65 points 
over the target.

Two: Your Apple Watch data over the past 14 days shows your resting heart rate 
has been elevated. It started around 72 beats per minute but has risen to 
88-95, which for you represents a concerning increase.

Three: When looked at together, high cholesterol plus elevated heart rate can 
indicate your heart is working harder than optimal. This is why both your chart 
and your doctor flagged this as a medium-priority alert.

Your doctor recommended three actions:
- Increase aerobic exercise
- Reduce dietary saturated fat
- Recheck your cholesterol in 6 weeks

These evidence-based recommendations are your next steps.'

Notice something crucial: every claim is backed by actual data. 
When the AI says 'elevated cholesterol,' it points to the specific blood test 
result. When it mentions heart rate, it references the wearable data.

This is AI healthcare done right: transparent, verifiable, trustworthy."

---

### SCENE 7: SECURITY & PRIVACY (40 seconds)
*[Brief security/privacy indicators visible on screen]*

"Underlying everything is enterprise-grade security.

DASS Health uses role-based access control. Patients only see their own data. 
Doctors only see patients on their roster. Other doctors cannot access another 
doctor's patients. This is not just good practice — it's HIPAA compliance.

All data is encrypted in transit and at rest. The system has undergone 
rigorous security testing to ensure no data leaks or cross-contamination 
between users.

For healthcare, security isn't optional. It's foundational."

---

### CLOSING NARRATION (30 seconds)
*[Logo appears with tagline]*

"Medical data is powerful. But only when it's understood and acted upon.

DASS Health brings together three critical pieces:
- Patient insights from uploaded medical records
- Real-time data from wearable devices
- AI-powered analysis that explains what it means

The result: proactive, personalized, evidence-based healthcare.

Patients get clarity. Doctors get complete context. Everyone gets better care.

This is DASS Health. Learn more at our website."

---

## PRODUCTION CHECKLIST

### PRE-RECORDING (Before you press Record)

**Environment Setup**
- [ ] Close all other applications (Slack, email, Chrome tabs)
- [ ] Enable Do Not Disturb mode (silence phone notifications)
- [ ] Set display resolution to exactly 1920x1080
- [ ] Disable screen saver
- [ ] Clear browser history/cache
- [ ] Test microphone and audio levels
- [ ] Have credentials written on paper next to monitor
- [ ] **[CRITICAL] Set up dual browser windows or mobile simulator:**
  - Option A: Two browser windows side-by-side (patient app, doctor dashboard)
  - Option B: Mobile device screen + browser window (record both with external camera or simulator)
  - Option C: Use screen division: Patient app (left 50%), Doctor app (right 50%)

**Technical Setup**
- [ ] OBS or screen recording software open and ready
- [ ] Backend server running (`uvicorn backend.main:app --reload`)
- [ ] Database populated with demo data
- [ ] Browser with patient and doctor portals open in separate windows
- [ ] Output file set to save location: `~/Videos/dass-demo-raw.mkv`

**Script Preparation**
- [ ] Print narration script or have it on separate monitor
- [ ] Read through script 2-3 times
- [ ] Time yourself reading it (should be 2.5-3.5 minutes)
- [ ] Mark sections you want to emphasize

**Dry Run**
- [ ] Do a practice run without recording
- [ ] Log in to patient account (smooth login, no typos)
- [ ] Navigate through each screen
- [ ] Log in to doctor account
- [ ] Check timing for each segment
- [ ] Verify no system crashes or slowdowns
- [ ] Note any issues to fix before actual recording

---

### RECORDING SETUP (Technical Details)

**OBS Configuration**

1. **Source:** Display Capture or Window Capture
   - Select your primary display/browser window
   - Resolution: 1920x1080

2. **Audio Capture:** Microphone Input
   - Device: USB Microphone (or built-in if unavailable)
   - Level: -6dB to 0dB (good balance)
   - Test by speaking - you should see audio meters move

3. **Output Settings**
   - Format: MP4 or MKV
   - Encoder: H264 (Default)
   - Bitrate: 6000 kbps (video), 192 kbps (audio)
   - File: `dass-demo-raw.mp4`

4. **Recording Quality**
   - Base of 1920×1080
   - Scale filter: Lanczos (high quality)
   - Frame rate: 30 fps
   - Quality: High

---

### RECORDING BREAKDOWN (Scene by Scene)

#### SEGMENT 1: INTRO + PATIENT LOGIN (5 minutes of footage)

**[00:00] Start recording**

Show black screen for 1 second.

**[00:01] Display DASS Health login screen**
- Wait 2 seconds
- Read from script: "Introducing DASS Health..." (30 seconds)
- Let narration play while screen visible

**[00:30] Click on patient login form**

**[00:35] Enter credentials slowly**
- Type: `patient.demo@dass.health` (pause between letters)
- Type password: `DemoPass123!` (pause between characters)
- Pause 2 seconds looking at form

**[01:00] Click "Login" button**

**[01:05] Wait for dashboard to load** (pause silently for 5 seconds)

**[01:10] Dashboard appears**

**[01:15] Scroll to "My Reports" section**
- Scroll smoothly, pause 2 seconds at each major element
- Point out (hover mouse over) blood test report
- Click on it to open

**[02:00] Show report details**
- Scroll through extracted lab results
- Pause 2-3 seconds on each abnormal finding:
  - Total Cholesterol: 245 (HIGH)
  - LDL: 165 (HIGH)  
  - Triglycerides: 185 (HIGH)
- Read key values aloud from script

**[03:00] Scroll to wearable data card**
- Show Apple Watch connected indicator
- Show heart rate trend chart
- Pause 2 seconds explaining (reading from script)

**[04:00] Take screenshot or pause 2-3 seconds**

**[04:30] Stop recording Segment 1**

---

#### SEGMENT 2: HEALTH ALERT (3 minutes of footage)

**[00:00] Start recording**

**[00:01] Scroll to Alerts section** OR **click Notifications bell**

**[00:05] Alert card appears**
- Title: "Elevated Heart Rate + High Cholesterol Pattern Detected"
- Show severity badge (MEDIUM, yellow color)

**[00:15] Click alert to expand**

**[00:30] Alert details visible**
- Description shows:
  - Blood test findings (cholesterol, LDL, triglycerides)
  - Wearable findings (elevated heart rate)
  - Clinical correlation
  - Recommendation

**[01:00] Pause and read alert content aloud** (40 seconds from script)

**[02:00] Scroll through full alert text**

**[02:30] Point out timestamp: "Triggered 14 days ago"**

**[02:45] Take final screenshot**

**[03:00] Stop recording Segment 2**

---

#### SEGMENT 3: DOCTOR DASHBOARD (5 minutes of footage)

**[00:00] Start recording**

**[00:01] Show doctor login screen in new browser tab**

**[00:10] Enter doctor credentials slowly**
- Email: `doctor.demo@dass.health`
- Password: `DemoPass123!`

**[00:30] Click Login**

**[00:35] Wait for doctor dashboard to load**

**[01:00] Doctor dashboard appears - show patient roster**
- List of patients
- Alex Chen card highlighted with alert badge

**[01:10] Click on "Alex Chen" patient card**

**[01:20] Patient summary page loads**
- Show sections one by one:
  - Patient info (name, age, DOB)
  - Medical history
  - Recent alerts
  - Lab results with charts

**[01:50] Point out blood test card**
- Show date: "Jan 10, 2025"
- Expand to show metrics:
  - Cholesterol bar chart
  - LDL bar chart
  - Triglycerides gauge

**[02:30] Scroll to wearable data section**
- Show 14-day heart rate trend
- Point out elevation over time

**[03:00] Scroll to clinical notes**
- Show doctor's notes created 7 days ago
- Read key recommendations:
  - Cardiologist referral
  - Lifestyle modifications
  - Follow-up labs in 6 weeks

**[03:50] Pause and read narration** (60 seconds from script)

**[04:50] Point at alert section one more time**

**[05:00] Stop recording Segment 3**

---

#### SEGMENT 4: AI CHAT (5 minutes of footage)

**[00:00] Start recording (back to patient portal)**

**[00:05] Scroll down to find "Ask AI" button OR "Chat" icon**

**[00:15] Click to open AI chat interface**

**[00:25] Chat window opens with input field**

**[00:35] Click in message input box**

**[00:40] Type slowly:** 
"Why did I get an alert for high heart rate?"

*[Pause 1-2 seconds after typing]*

**[01:00] Click Send button**

**[01:05] Show "Generating response..." or loading animation**

**[01:10-02:00] AI generates and streams response**
- Response appears word by word or paragraph by paragraph
- Let it complete fully

**[02:05] Full response visible on screen**
- Should include:
  - Explanation of blood test findings
  - Explanation of wearable findings
  - Clinical correlation
  - Recommended next steps

**[02:10] Scroll down to see more of response**

**[02:40] Scroll to citations section**
- Show source documents cited
- Expand citations (if clickable)
- Point to specific sources

**[03:15] Read narration aloud** (80 seconds from script)
*[Emphasize transparency and trust]*

**[04:45] Take final screenshot**

**[05:00] Stop recording Segment 4**

---

#### SEGMENT 5: SECURITY (2 minutes of footage)

**[00:00] Start recording**

**[00:10] Show security/HIPAA badge (if visible on screen)**

**[00:20] Brief explanation from script** (40 seconds)
- Talk about role-based access
- Encryption
- HIPAA compliance

**[00:60] Show privacy settings** (if available in UI)

**[01:30] Pause and emphasize security message**

**[02:00] Stop recording Segment 5**

---

### NARRATION RECORDING (Separate from video)

**Do NOT record narration while screen recording.**  
Record audio separately for better quality.

1. **Open Audacity** (free audio recording software)
2. **Settings:**
   - Project rate: 44100 Hz
   - Recording format: Stereo / 16-bit
   - Input: USB Microphone

3. **For each scene, record separately:**
   - Scene 1 intro: 30 seconds
   - Scene 2 patient narration: 50 seconds
   - Scene 3 alert narration: 40 seconds
   - Scene 4 doctor narration: 60 seconds
   - Scene 5 AI narration: 80 seconds
   - Closing narration: 30 seconds

4. **Recording tips:**
   - Speak slowly and clearly (not too fast)
   - Pause between sentences for natural timing
   - Take breaths
   - If you mess up, stop and start again
   - Record multiple takes and pick the best

5. **Export:** WAV or MP3 for each segment

---

### POST-RECORDING (After hitting Stop)

- [ ] Verify file was created (~50-100 MB for 5-minute 1080p video)
- [ ] Play back a portion to check audio/video sync
- [ ] Check no freezes or corrupted frames
- [ ] Move file to edit directory
- [ ] Back up original footage (in case editing goes wrong)
- [ ] Document recording date/time and issues encountered

---

## EDITING CHECKLIST

### Video Editor Setup

**Install Free Option:**
```bash
# macOS
brew install davinci-resolve

# Linux
Download from blackmagicdesign.com

# Windows
Download from blackmagicdesign.com
```

### Key Feature: Side-by-Side / Alternating Mobile App & Web Dashboard

**This is a CRITICAL requirement:** Your final video must clearly show both the Patient Mobile App and the Doctor Web Dashboard, either:
- **Side-by-side:** Patient app on left half, doctor dashboard on right half of screen
- **Alternating:** Cut between apps with smooth transitions every 10-30 seconds

This demonstrates the full system value: how patient and doctor see the same case from different perspectives.

### Editing Steps

1. **Import video** → `dass-demo-raw.mp4`
2. **Create timeline** (1080p, 30fps, 24s timebase)
3. **Add clips in order with side-by-side layout:**
   
   **LAYOUT OPTIONS** (Choose one):
   
   **Option A: Side-by-Side Split Screen**
   - Patient app on left half (50% width)
   - Doctor dashboard on right half (50% width)
   - Show both simultaneously for comparison
   - Use this for Segments 1-4 to demonstrate parallel workflow
   
   **Option B: Alternating Cut (Recommended for smooth editing)**
   - Patient app segment: 20-30 seconds
   - Cut to doctor dashboard: 20-30 seconds
   - Repeat pattern showing same data from both perspectives
   - Provides visual variety and clearer focus
   
   **Timeline structure:**
   - [0-2m] Intro + Patient login and report upload
   - [2-3.5m] Patient views wearable data → Cut to → Doctor sees same patient on dashboard
   - [3.5-5m] Alert appears on patient side → Cut to → Doctor reviews alert
   - [5-6.5m] Patient AI chat explanation → (Optional: Show doctor notes for context)
   - [6.5-7.5m] Security overview

4. **Trim**
   - Remove black frames at start/end
   - Remove any major pauses (keep some breathing room)
   - Target total 3-5 minutes

5. **CREATE SIDE-BY-SIDE LAYOUT** (DaVinci Resolve instructions)
   
   **For Side-by-Side Split Screen:**
   - Drag first video clip (patient app) to timeline
   - Right-click clip → Create Compound Clip
   - In Inspector panel: Set Scale to 50% and Position to Left (X: -25%)
   - Drag second video clip (doctor dashboard) to same timeline track above first
   - Right-click → Create Compound Clip
   - Set Scale to 50% and Position to Right (X: +25%)
   - Adjust timing so both clips play simultaneously
   
   **For Alternating Cut:**
   - Place patient app clip in timeline: 20 seconds
   - Add Cross-Dissolve transition: 1 second
   - Place doctor dashboard clip: 20 seconds
   - Add Cross-Dissolve transition: 1 second
   - Repeat pattern 2-3 times
   - Label each cut with lower third text ("Patient View" / "Doctor View")

6. **Add intro title card** (5 seconds)
   - Text: "DASS HEALTH"
   - Subtitle: "AI-Powered Medical Platform"
   - Fade in / fade out

7. **Add background music**
   - Download royalty-free: Epidemic Sound OR YouTube Audio Library
   - Place on audio track below narration
   - Volume: -15dB
   - Fade in at start, fade out 5 seconds before end

8. **Layer narration audio**
   - Import WAV files
   - Place on audio track above video
   - Sync with screen actions
   - Volume: 0dB (Unity)
   - Adjust timing so narration matches visuals

9. **Add scene transitions**
   - Between major sections: Cross-dissolve (1 second)
   - Fade to black between patient/doctor views

10. **Add lower thirds** (text overlay)
   - For ~3 seconds per label:
     - "Alex Chen - Patient"
     - "Dr. Sarah Mitchell - Physician"
     - "Apple Watch Data"
     - "Patient View" (if using alternating cuts)
     - "Doctor View" (if using alternating cuts)

11. **Color correction**
    - Right-click clip > Color Correction
    - Auto-adjust brightness/contrast
    - Ensure consistent across all segments

12. **Final review**
    - Play full timeline without stopping
    - Check audio sync
    - Verify no artifacts
    - Check duration (3-5 minutes)

### Export Settings

```
Format: MP4
Codec: H.264
Profile: High
Level: 4.2
Resolution: 1920×1080
Frame rate: 30 fps
Bitrate: 6000 kbps (variable)
Audio codec: AAC
Audio bitrate: 192 kbps
Audio track: Stereo

Output: DASS-Health-MVP-Demo-FINAL.mp4
```

---

## UPLOAD CHECKLIST

Before sharing video publicly:

- [ ] Video duration is 3-5 minutes (verify)
- [ ] Sound quality is clear (narration audible)
- [ ] No sensitive credentials visible
- [ ] No personal information exposed
- [ ] Video is 1080p minimum quality
- [ ] File size reasonable (<500 MB)

**Upload to YouTube (Recommended):**

1. Go to `youtube.com/studio`
2. Click "Create" > "Upload video"
3. Select `DASS-Health-MVP-Demo-FINAL.mp4`
4. Fill in:
   - **Title:** "DASS Health MVP - AI-Powered Health Platform Demo"
   - **Description:** *(See template below)*
   - **Privacy:** Unlisted (only people with link can view)
   - **Category:** Science & Technology
5. Click "Publish"
6. Copy shareable link
7. Add link to README

**YouTube Description Template:**

```
DASS Health MVP Demo

Duration: 3-5 minutes

This demo showcases DASS Health, an AI-powered healthcare platform that 
connects patients, doctors, and wearable data for proactive health management.

Scenes:
0:00 - Introduction
0:30 - Patient Login & Dashboard
1:30 - Health Alert Notification
2:30 - Doctor Dashboard View
4:00 - AI-Powered Chat Explanation
4:45 - Security & Privacy Features
5:00 - Closing

Demo Scenario:
Patient uploads blood test → System detects elevated cholesterol + heart rate 
pattern → Alert generated → Doctor reviews → Patient asks AI "Why?" → AI 
explains with source citations

Key Features:
✓ Patient portal with report uploads
✓ Wearable data integration
✓ AI-powered multi-metric alerts
✓ Doctor dashboard for patient overview
✓ Explainable AI with citation sources
✓ HIPAA-compliant security
✓ Role-based access control

Learn more at [project URL]
```

---

## FINAL VERIFICATION

Before calling the project complete:

```
DATABASE
☐ Golden path data seeded (patient, reports, labs, alerts)
☐ Verification queries passed (6 records created)
☐ No duplicate alerts or labs
☐ All timestamps realistic (30, 21, 14, 7 days ago)

VIDEO
☐ Duration: 3-5 minutes (verify with video player)
☐ Resolution: 1080p (1920x1080)
☐ Frame rate: 30 fps
☐ Codec: H.264 (MP4)
☐ Audio: Clear narration + background music
☐ No freezes or artifacts
☐ Synchronized narration with screen actions

SHARING
☐ Video successfully uploaded to YouTube/Vimeo
☐ Sharable link generated
☐ Link works (tested with fresh browser)
☐ Link provided in README

DOCUMENTATION
☐ Narration script finalized
☐ Production notes documented
☐ Troubleshooting guide created
☐ Credentials securely stored
☐ All deliverables listed and verified
```

---

*
*