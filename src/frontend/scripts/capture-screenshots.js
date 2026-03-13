const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const BASE_URL = process.env.BASE_URL || 'http://127.0.0.1:4173';
const ROOT = path.resolve(__dirname, '../../..');
const SCREENSHOT_DIR = path.join(ROOT, 'docs', 'screenshots');
const SAMPLE_REPORT = path.join(
  ROOT,
  'src',
  'sample_reports',
  'iron_deficiency',
  'iron_deficiency__Riya_Sharma__28F.pdf'
);

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

async function waitForStable(page, timeout = 500) {
  await page.waitForLoadState('domcontentloaded');
  await page.waitForTimeout(timeout);
}

async function captureReports(page, results) {
  await page.goto(`${BASE_URL}/reports.html`, { waitUntil: 'networkidle' });
  await waitForStable(page);

  await page.setInputFiles('#file-input', SAMPLE_REPORT);
  await page.waitForFunction(() => {
    const el = document.getElementById('upload-status');
    return el && el.textContent.includes('uploaded');
  }, { timeout: 5000 });

  await page.locator('#timeline-wrap').scrollIntoViewIfNeeded();
  await page.screenshot({
    path: path.join(SCREENSHOT_DIR, 'report-timeline.png'),
    fullPage: true,
  });

  results.push({
    step: 'Upload report + view timeline',
    status: 'passed',
    evidence: 'Upload success text appeared and timeline screenshot saved.',
  });
}

async function captureAlerts(page, results) {
  await page.goto(`${BASE_URL}/alerts.html`, { waitUntil: 'networkidle' });
  await waitForStable(page);

  const firstAlertHeader = page.locator('.alert-card-header').first();
  await firstAlertHeader.click();
  await page.waitForSelector('.alert-body.open');

  await page.screenshot({
    path: path.join(SCREENSHOT_DIR, 'alerts-dashboard.png'),
    fullPage: true,
  });

  results.push({
    step: 'View alerts + explanation',
    status: 'passed',
    evidence: 'Alert detail drawer expanded and screenshot saved.',
  });
}

async function captureChat(page, results) {
  await page.goto(`${BASE_URL}/chat.html`, { waitUntil: 'networkidle' });
  await waitForStable(page);

  await page.fill('#chat-input', 'What does my haemoglobin reading mean?');
  await page.getByRole('button', { name: 'Send' }).click();
  await page.waitForFunction(() => {
    return document.querySelectorAll('.chat-msg.assistant').length >= 1;
  }, { timeout: 10000 });
  await page.waitForTimeout(1200);

  await page.locator('#context-section').scrollIntoViewIfNeeded();
  await page.screenshot({
    path: path.join(SCREENSHOT_DIR, 'ai-response-view.png'),
    fullPage: true,
  });

  results.push({
    step: 'Ask AI question',
    status: 'passed',
    evidence: 'Assistant response with citations rendered and screenshot saved.',
  });
}

async function captureDoctor(page, results) {
  await page.goto(`${BASE_URL}/doctor.html`, { waitUntil: 'networkidle' });
  await waitForStable(page);

  await page.screenshot({
    path: path.join(SCREENSHOT_DIR, 'doctor-view.png'),
    fullPage: true,
  });

  results.push({
    step: 'View doctor dashboard',
    status: 'passed',
    evidence: 'Doctor page rendered and screenshot saved.',
  });
}

async function main() {
  ensureDir(SCREENSHOT_DIR);

  if (!fs.existsSync(SAMPLE_REPORT)) {
    throw new Error(`Sample report not found: ${SAMPLE_REPORT}`);
  }

  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1400 } });
  const results = [];

  try {
    await captureReports(page, results);
    await captureAlerts(page, results);
    await captureChat(page, results);
    await captureDoctor(page, results);

    const summary = {
      capturedAt: new Date().toISOString(),
      baseUrl: BASE_URL,
      screenshots: [
        'docs/screenshots/report-timeline.png',
        'docs/screenshots/alerts-dashboard.png',
        'docs/screenshots/ai-response-view.png',
        'docs/screenshots/doctor-view.png',
      ],
      demoFlowResults: results,
    };

    fs.writeFileSync(
      path.join(ROOT, 'docs', 'screenshots', 'demo-flow-results.json'),
      JSON.stringify(summary, null, 2)
    );

    console.log(JSON.stringify(summary, null, 2));
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
