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

