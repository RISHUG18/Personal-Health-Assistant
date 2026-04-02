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

