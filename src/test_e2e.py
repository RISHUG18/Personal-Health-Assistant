import io, time, requests

BASE = "http://localhost:8000"
TS   = int(time.time())

def p(label, r):
    print(f"\n{'─'*55}")
    print(f"  {label}  [{r.status_code}]")
    try:    print(f"  {r.json()}")
    except: print(f"  {r.text[:300]}")

# 1. Register patient
r = requests.post(f"{BASE}/auth/register", json={
    "email": f"patient_{TS}@test.com", "password": "Test123!",
    "full_name": "Priya Patel", "role": "patient"})
p("Register patient", r)
d = r.json()
PID   = d["user_id"]
PTOK  = d["access_token"]

# 2. Register doctor
r = requests.post(f"{BASE}/auth/register", json={
    "email": f"doctor_{TS}@test.com", "password": "Test123!",
    "full_name": "Dr. Arjun", "role": "doctor"})
p("Register doctor", r)
d = r.json()
DID   = d["user_id"]
DTOK  = d["access_token"]

AUTH = {"Authorization": f"Bearer {DTOK}"}

# 3. Doctor adds patient
r = requests.post(f"{BASE}/api/v1/doctor/patients",
    headers=AUTH, json={"patient_id": PID})
p("Doctor adds patient", r)

# 4. List patients
r = requests.get(f"{BASE}/api/v1/doctor/patients", headers=AUTH)
p("Doctor lists patients", r)

# 5. Patient summary
r = requests.get(f"{BASE}/api/v1/doctor/patients/{PID}/summary", headers=AUTH)
p("Patient summary", r)

# 6. Patient reports
r = requests.get(f"{BASE}/api/v1/doctor/patients/{PID}/reports", headers=AUTH)
p("Patient reports", r)

# 7. Evaluate alerts
r = requests.post(f"{BASE}/api/v1/doctor/patients/{PID}/evaluate-alerts",
    headers=AUTH, json={})
p("Evaluate alerts", r)

# 8. Ingest report
dummy = b"%PDF-1.4 1 0 obj<</Type/Catalog>>endobj xref 0 0 trailer<<>>%%EOF"
r = requests.post(f"{BASE}/reports/ingest",
    files={"file": ("report.pdf", io.BytesIO(dummy), "application/pdf")},
    data={"user_id": PID, "user_name": "Priya Patel"})
p("Ingest report (202)", r)
RID = r.json().get("report_id", "")

# 9. Poll status
print(f"\n  Polling report status (15s)...")
time.sleep(15)
r = requests.get(f"{BASE}/reports/status/{RID}")
p(f"Report status [{RID[:8]}...]", r)

# 10. Remove patient
r = requests.delete(f"{BASE}/api/v1/doctor/patients/{PID}", headers=AUTH)
p("Doctor removes patient", r)

print(f"\n{'═'*55}\n  Done  patient={PID[:8]}  doctor={DID[:8]}\n{'═'*55}")
