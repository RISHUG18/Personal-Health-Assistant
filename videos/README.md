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

