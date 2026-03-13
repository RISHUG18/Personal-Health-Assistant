# Demo Flow Test Notes

Date: 2026-03-13

## Screenshots captured

- `docs/screenshots/alerts-dashboard.png`
- `docs/screenshots/ai-response-view.png`
- `docs/screenshots/report-timeline.png`

Machine-generated capture summary:
- `docs/screenshots/demo-flow-results.json`

## Demo flow executed

### 1. Upload report
- Opened `reports.html`
- Uploaded sample PDF:
  - `src/sample_reports/iron_deficiency/iron_deficiency__Riya_Sharma__28F.pdf`
- Verified upload success message rendered
- Captured timeline screenshot

### 2. View alerts
- Opened `alerts.html`
- Expanded the first alert card explanation drawer
- Verified evidence and explanation content rendered
- Captured alerts dashboard screenshot

### 3. Ask AI question
- Opened `chat.html`
- Asked: `What does my haemoglobin reading mean?`
- Verified assistant response rendered with citations
- Captured AI response screenshot

### 4. View explanation
- Explanation was validated through the expanded alert card in `alerts.html`
- Evidence section and source references were visible in the captured alert dashboard state

## Result

All requested screenshot captures completed successfully, and the demo flow executed without blocking issues in the static frontend demo.
