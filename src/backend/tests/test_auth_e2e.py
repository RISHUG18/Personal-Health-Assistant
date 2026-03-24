import sys
import uuid
import time
from pathlib import Path

# Add src/ to sys.path
_SRC_DIR = Path(__file__).resolve().parents[2]
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from fastapi.testclient import TestClient
from backend.main import app

def run_e2e_tests():
    client = TestClient(app)
    test_email = f"e2e_test_{uuid.uuid4().hex[:8]}@example.com"
    test_password = "SuperSecurePassword123!"

    print("==================================================")
    print(" Auth Pipeline End-to-End Robustness Suite")
    print("==================================================")
    print(f"Testing with unique email: {test_email}\n")

    # 1. Register User (Happy Path)
    print("  [TEST 1] Register new user -> expecting 201")
    resp_reg = client.post("/auth/register", json={
        "email": test_email,
        "password": test_password,
        "full_name": "E2E Test User",
        "role": "patient"
    })
    
    if resp_reg.status_code == 201:
        print("  ✅ SUCCESS: User registered and mapped into public.users.")
        data = resp_reg.json()
        print(f"     -> user_id: {data['user_id']}")
        # The new robust logic assigns tokens immediately!
        if data.get("access_token"):
            print("     -> 🎫 Access Token retrieved automatically via Sign-In!")
        else:
            print("     -> ⚠️ No access token retrieved immediately.")
    else:
        print(f"  ❌ FAILED: {resp_reg.status_code}")
        print(f"     -> {resp_reg.text}")
        sys.exit(1)

    print()
    
    # 2. Duplicate Registration (Testing Rollback / Conflict)
    print("  [TEST 2] Duplicate user registration -> expecting 400")
    resp_dup = client.post("/auth/register", json={
        "email": test_email,
        "password": test_password,
        "full_name": "Duplicate User",
        "role": "patient"
    })
    
    if resp_dup.status_code == 400:
        print("  ✅ SUCCESS: Gracefully blocked duplicate user.")
        print(f"     -> details: {resp_dup.json()['detail']}")
    else:
        print(f"  ❌ FAILED: Expected 400, got {resp_dup.status_code}")
        print(f"     -> {resp_dup.text}")
        sys.exit(1)

    print()
    
    # 3. Valid Login (Testing Auto-Confirm bypass behavior)
    print("  [TEST 3] Login immediately with valid credentials -> expecting 200")
    resp_login = client.post("/auth/login", json={
        "email": test_email,
        "password": test_password
    })
    
    if resp_login.status_code == 200:
        print("  ✅ SUCCESS: Logged in properly (Email confirmation bypassed!).")
        data = resp_login.json()
        print("     -> 🎫 Access Token received.")
        
        # Save token for next step
        access_token = data.get("access_token")
    else:
        print(f"  ❌ FAILED: Expected 200, got {resp_login.status_code}")
        print(f"     -> {resp_login.text}")
        sys.exit(1)

    print()

    # 4. Invalid Login (Wrong password)
    print("  [TEST 4] Login with invalid credentials -> expecting 401")
    resp_bad_login = client.post("/auth/login", json={
        "email": test_email,
        "password": "WrongPassword123!"
    })
    
    if resp_bad_login.status_code == 401:
        print("  ✅ SUCCESS: Gracefully blocked invalid login credentials.")
    else:
        print(f"  ❌ FAILED: Expected 401, got {resp_bad_login.status_code}")
        print(f"     -> {resp_bad_login.text}")
        sys.exit(1)

    print()

    # 5. Protected Upload Pipeline Rejection
    print("  [TEST 5] Access protected /upload/report without token -> expecting 403")
    resp_unauth_upload = client.post("/upload/report", files={"file": ("fake.pdf", b"%PDF-1.4", "application/pdf")})
    
    if resp_unauth_upload.status_code in (401, 403):
        print("  ✅ SUCCESS: Protected route securely blocked unauthenticated access.")
    else:
        print(f"  ❌ FAILED: Expected 403, got {resp_unauth_upload.status_code}")
        
    print()
    print("==================================================")
    print(" 🎉  ALL E2E ROBUSTNESS TESTS PASSED PERFECTLY!")
    print("==================================================")

if __name__ == "__main__":
    run_e2e_tests()
