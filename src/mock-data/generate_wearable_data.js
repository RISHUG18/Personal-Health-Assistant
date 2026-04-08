#!/usr/bin/env node

/**
 * Wearable Data Generator for Testing
 * Generates realistic 7-day minute-by-minute heart rate and sleep data
 * 
 * This script creates a JSON payload with realistic circadian patterns,
 * activity spikes, and sleep cycles for testing Person 3's wearable API ingestion.
 * 
 * Usage:
 *   node generate_wearable_data.js [--output=payload.json] [--patient-id=pat-001]
 */

const fs = require('fs');
const path = require('path');

// Parse command-line arguments
const args = process.argv.slice(2);
let outputFile = path.join(__dirname, 'wearable_payload.json');
let patientId = 'pat-001';

args.forEach(arg => {
  if (arg.startsWith('--output=')) {
    outputFile = arg.split('=')[1];
  }
  if (arg.startsWith('--patient-id=')) {
    patientId = arg.split('=')[1];
  }
});

// Constants for realistic data generation
const SLEEP_START_HOUR = 23;
const SLEEP_END_HOUR = 7;
const RESTING_HR = 65;
const ACTIVE_HR = 100;
const HR_MIN = 47;
const HR_MAX = 135;

/**
 * Generate heart rate for a specific hour considering circadian patterns
 */
function generateHeartRateForHour(hour, isAwake, activityLevel = 0) {
  let baseHR = RESTING_HR;
  
  // Circadian rhythm: higher HR in afternoon/evening
  if (hour >= 8 && hour <= 16) {
    baseHR += 8; // Afternoon peak
  } else if (hour >= 17 && hour <= 21) {
    baseHR += 5; // Evening
  } else if (hour >= 22 || hour <= 6) {
    baseHR -= 8; // Night dip
  }
  
  // Activity level boost (0-1)
  const activityBoost = activityLevel * (ACTIVE_HR - RESTING_HR);
  baseHR += activityBoost;
  
  // Add small random variation
  const variation = (Math.random() - 0.5) * 6;
  baseHR += variation;
  
  // Clamp to realistic range
  return Math.max(HR_MIN, Math.min(HR_MAX, Math.round(baseHR)));
}

/**
 * Generate sleep stage (awake, light, deep, rem)
 */
function generateSleepStage(minuteInSleep) {
  const cycleLength = 90; // Sleep cycles ~90 minutes
  const positionInCycle = minuteInSleep % cycleLength;
  
  if (positionInCycle < 10) return 'awake';
  if (positionInCycle < 20) return 'light';
  if (positionInCycle < 60) return 'deep';
  if (positionInCycle < 85) return 'rem';
  return 'light';
}

/**
 * Generate 7 days of wearable data
 */
function generateWearablePayload() {
  const startDate = new Date('2026-03-31'); // Start from March 31
  const dataPoints = [];
  const summary = {
    totalHeartRateReadings: 0,
    totalSleepReadings: 0,
    avgHeartRate: 0,
    minHeartRate: HR_MAX,
    maxHeartRate: HR_MIN,
    avgSleepPerNight: 0,
    totalSleepMinutes: 0
  };
  
  // Generate 7 days
  for (let day = 0; day < 7; day++) {
    const currentDate = new Date(startDate);
    currentDate.setDate(currentDate.getDate() + day);
    const dateString = currentDate.toISOString().split('T')[0];
    
    // Generate all 1440 minutes of the day
    for (let minute = 0; minute < 1440; minute++) {
      const hour = Math.floor(minute / 60);
      const minuteOfHour = minute % 60;
      
      // Determine if person is awake or sleeping (approximately)
      const isSleepTime = (hour >= SLEEP_START_HOUR || hour < SLEEP_END_HOUR);
      
      // Generate activity level (20% chance of activity during awake hours)
      const activityLevel = !isSleepTime && Math.random() < 0.15 ? Math.random() * 0.8 : 0;
      
      // Generate heart rate
      const heartRate = generateHeartRateForHour(hour, !isSleepTime, activityLevel);
      
      // Generate sleep data
      let sleepData = null;
      if (isSleepTime) {
        // Calculate minutes into sleep period
        let minutesIntoSleep = 0;
        if (hour >= SLEEP_START_HOUR) {
          minutesIntoSleep = (24 - SLEEP_START_HOUR) * 60 + hour * 60 + minuteOfHour;
        } else {
          minutesIntoSleep = (hour * 60) + minuteOfHour;
        }
        
        sleepData = {
          stage: generateSleepStage(minutesIntoSleep),
          confidence: 0.92 + Math.random() * 0.07
        };
        
        summary.totalSleepReadings++;
        summary.totalSleepMinutes++;
      }
      
      // Create data point
      const timestamp = new Date(currentDate);
      timestamp.setHours(hour, minuteOfHour, 0, 0);
      
      dataPoints.push({
        timestamp: timestamp.toISOString(),
        date: dateString,
        hour: hour,
        heartRate: heartRate,
        heartRateConfidence: 0.94 + Math.random() * 0.05,
        sleep: sleepData,
        deviceBattery: 85 + Math.random() * 15
      });
      
      // Update summary stats
      summary.totalHeartRateReadings++;
      summary.avgHeartRate += heartRate;
      summary.minHeartRate = Math.min(summary.minHeartRate, heartRate);
      summary.maxHeartRate = Math.max(summary.maxHeartRate, heartRate);
    }
  }
  
  // Calculate averages
  summary.avgHeartRate = Math.round(summary.avgHeartRate / summary.totalHeartRateReadings);
  summary.avgSleepPerNight = Math.round(summary.totalSleepMinutes / 7 / 60 * 10) / 10; // hours per night
  
  // Build final payload
  const payload = {
    metadata: {
      patientId: patientId,
      deviceType: "Fitbit Sense 2",
      deviceId: "device-" + Math.random().toString(36).substr(2, 9),
      generatedAt: new Date().toISOString(),
      dataSource: "wearable_mock_generator",
      periodStart: "2026-03-31",
      periodEnd: "2026-04-06",
      totalDays: 7,
      granularity: "minute"
    },
    summary: summary,
    dataPoints: dataPoints
  };
  
  return payload;
}

// Generate and save
console.log('🏃 Generating 7-day wearable dataset...\n');

try {
  const payload = generateWearablePayload();
  
  const outputDir = path.dirname(outputFile);
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }
  
  fs.writeFileSync(outputFile, JSON.stringify(payload, null, 2));
  
  const stats = fs.statSync(outputFile);
  const fileSizeKB = (stats.size / 1024).toFixed(2);
  
  console.log('✅ Successfully generated wearable payload!');
  console.log(`📊 File: ${outputFile}`);
  console.log(`📈 Size: ${fileSizeKB} KB`);
  console.log(`📍 Patient ID: ${patientId}`);
  console.log(`⏱️  Total data points: ${payload.dataPoints.length.toLocaleString()}`);
  console.log(`💓 Avg heart rate: ${payload.summary.avgHeartRate} bpm`);
  console.log(`😴 Avg sleep: ${payload.summary.avgSleepPerNight} hours/night`);
  console.log(`\n✨ Ready for API ingestion testing!\n`);
  
} catch (err) {
  console.error(`❌ Error generating payload: ${err.message}`);
  process.exit(1);
}
