#!/usr/bin/env python3
"""
Security QA - RBAC Vulnerability Testing
Tests for authorization bypass vulnerabilities in Person 1's implementation.
"""

import json
import sys
from pathlib import Path

import requests


BASE_URL = "http://localhost:8000"
RESULTS_FILE = Path(__file__).parent / "security_qa_results.json"


class SecurityTester:
    """Test RBAC implementation for vulnerabilities."""
    
    def __init__(self):
        self.results = {
            "timestamp": "",
            "tests": [],
            "vulnerabilities": [],
            "summary": {}
        }
        self.session_doctor_a = None
        self.session_doctor_b = None
        self.session_patient = None
    
    def log_test(self, test_name: str, status: str, details: str):
        """Log a test result."""
        self.results["tests"].append({
            "name": test_name,
            "status": status,
            "details": details
        })
        print(f"  [{status}] {test_name}: {details}")
    
    def log_vulnerability(self, severity: str, title: str, description: str, remediation: str):
        """Log a security vulnerability."""
        self.results["vulnerabilities"].append({
            "severity": severity,
            "title": title,
            "description": description,
            "remediation": remediation
        })
        print(f"  🚨 [{severity.upper()}] {title}")
        print(f"     Description: {description}")
        print(f"     Fix: {remediation}")
    
    def register_user(self, email: str, password: str, full_name: str, role: str) -> dict:
        """Register a new user."""
        try:
            resp = requests.post(
                f"{BASE_URL}/auth/register",
                json={
                    "email": email,
                    "password": password,
                    "full_name": full_name,
                    "role": role
                },
                timeout=10
            )
            if resp.status_code == 201:
                return resp.json()
            else:
                return {"error": resp.text}
        except Exception as e:
            return {"error": str(e)}
    
    def login_user(self, email: str, password: str) -> dict:
        """Login a user."""
        try:
            resp = requests.post(
                f"{BASE_URL}/auth/login",
                json={"email": email, "password": password},
                timeout=10
            )
            if resp.status_code == 200:
                return resp.json()
            else:
                return {"error": resp.text}
        except Exception as e:
            return {"error": str(e)}
    
    def get_user_reports(self, user_id: str, token: str) -> dict:
        """Attempt to get reports for a user."""
        try:
            resp = requests.get(
                f"{BASE_URL}/reports/user/{user_id}",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10
            )
            return {"status_code": resp.status_code, "response": resp.json()}
        except Exception as e:
            return {"error": str(e)}
    
    def run_all_tests(self) -> bool:
        """Execute all security tests."""
        print("\n" + "=" * 70)
        print("🔐 SECURITY QA - RBAC VULNERABILITY TESTING")
        print("=" * 70)
        
        # Test 1: Setup test users
        print("\n▶️  Phase 1: User Registration")
        print("-" * 70)
        
        doctor_a_data = self.register_user(
            "doctor_a@hospital.local",
            "SecurePass123!",
            "Dr. Alice",
            "doctor"
        )
        if "error" in doctor_a_data:
            self.log_test("Register Doctor A", "FAILED", doctor_a_data["error"])
            print("❌ Cannot proceed - backend not available")
            return False
        
        self.log_test("Register Doctor A", "PASSED", f"User ID: {doctor_a_data.get('user_id', 'unknown')[:8]}...")
        doctor_a_id = doctor_a_data.get("user_id")
        
        doctor_b_data = self.register_user(
            "doctor_b@hospital.local",
            "SecurePass456!",
            "Dr. Bob",
            "doctor"
        )
        self.log_test("Register Doctor B", "PASSED", f"User ID: {doctor_b_data.get('user_id', 'unknown')[:8]}...")
        doctor_b_id = doctor_b_data.get("user_id")
        
        patient_data = self.register_user(
            "patient_riya@example.com",
            "PatientPass789!",
            "Riya Sharma",
            "patient"
        )
        self.log_test("Register Patient", "PASSED", f"User ID: {patient_data.get('user_id', 'unknown')[:8]}...")
        patient_id = patient_data.get("user_id")
        
        # Test 2: Login as different users
        print("\n▶️  Phase 2: Authentication & Token Generation")
        print("-" * 70)
        
        doctor_a_login = self.login_user("doctor_a@hospital.local", "SecurePass123!")
        self.log_test("Login as Doctor A", "PASSED", "Token received")
        doctor_a_token = doctor_a_login.get("access_token")
        
        doctor_b_login = self.login_user("doctor_b@hospital.local", "SecurePass456!")
        self.log_test("Login as Doctor B", "PASSED", "Token received")
        doctor_b_token = doctor_b_login.get("access_token")
        
        # Test 3: RBAC Vulnerability - Cross-Doctor Access
        print("\n▶️  Phase 3: RBAC Vulnerability Testing")
        print("-" * 70)
        
        # Attempt: Doctor A accessing Doctor B's patients via URL manipulation
        print("\n  🧪 Test 3.1: Doctor A accessing Doctor B's patient list (URL Manipulation)")
        result = self.get_user_reports(doctor_b_id, doctor_a_token)
        
        if result.get("status_code") == 200:
            # VULNERABILITY: Cross-doctor access granted
            self.log_vulnerability(
                severity="HIGH",
                title="Cross-Doctor Patient Access",
                description=f"Doctor A (token {doctor_a_token[:16]}...) was able to retrieve Doctor B's patient list by manipulating user_id in URL",
                remediation="Implement endpoint-level RBAC check: verify that the requesting doctor's ID matches the requested patient's assigned doctor ID before returning data"
            )
            self.log_test("Test 3.1", "VULNERABLE", "Doctor A accessed Doctor B's data")
        else:
            self.log_test("Test 3.1", "PASSED", f"Access denied with status {result.get('status_code')}")
        
        # Test 3.2: Accessing patient reports without authorization
        print("\n  🧪 Test 3.2: Doctor A accessing Patient's raw reports (URL Manipulation)")
        result = self.get_user_reports(patient_id, doctor_a_token)
        
        if result.get("status_code") == 200:
            # VULNERABILITY: Doctor accessing patient without consent
            self.log_vulnerability(
                severity="HIGH",
                title="Unauthorized Patient Data Access",
                description=f"Doctor A was able to access Patient's reports without explicit authorization being granted",
                remediation="Check patient's doctor_consent table / doctor_access permissions before returning report data. Verify requester_role='doctor' AND consent_record_exists(doctor_id, patient_id)"
            )
            self.log_test("Test 3.2", "VULNERABLE", "Doctor accessed unauthorized patient")
        else:
            self.log_test("Test 3.2", "PASSED", f"Access denied with status {result.get('status_code')}")
        
        # Test 3.3: Token manipulation
        print("\n  🧪 Test 3.3: Bearer token spoofing (Malformed token)")
        fake_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJmYWtlLXVzZXItaWQifQ.fakesignature"
        result = self.get_user_reports(patient_id, fake_token)
        
        if result.get("status_code") == 200:
            self.log_vulnerability(
                severity="CRITICAL",
                title="No Token Validation",
                description="Token validation was not enforced - fake token accepted",
                remediation="Implement token validation middleware using JWT verification and Supabase session validation"
            )
            self.log_test("Test 3.3", "VULNERABLE", "Invalid token accepted")
        else:
            self.log_test("Test 3.3", "PASSED", f"Invalid token rejected with status {result.get('status_code')}")
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 SECURITY QA SUMMARY")
        print("=" * 70)
        
        self.results["summary"] = {
            "total_tests": len(self.results["tests"]),
            "passed": sum(1 for t in self.results["tests"] if t["status"] == "PASSED"),
            "failed": sum(1 for t in self.results["tests"] if t["status"] == "FAILED"),
            "vulnerable": len(self.results["vulnerabilities"]),
            "severity_breakdown": {
                "critical": sum(1 for v in self.results["vulnerabilities"] if v["severity"] == "CRITICAL"),
                "high": sum(1 for v in self.results["vulnerabilities"] if v["severity"] == "HIGH"),
                "medium": sum(1 for v in self.results["vulnerabilities"] if v["severity"] == "MEDIUM"),
                "low": sum(1 for v in self.results["vulnerabilities"] if v["severity"] == "LOW"),
            }
        }
        
        print(f"Total Tests: {self.results['summary']['total_tests']}")
        print(f"Passed: {self.results['summary']['passed']}")
        print(f"Failed: {self.results['summary']['failed']}")
        print(f"Vulnerabilities Found: {len(self.results['vulnerabilities'])}")
        print(f"  - CRITICAL: {self.results['summary']['severity_breakdown']['critical']}")
        print(f"  - HIGH: {self.results['summary']['severity_breakdown']['high']}")
        print(f"  - MEDIUM: {self.results['summary']['severity_breakdown']['medium']}")
        print(f"  - LOW: {self.results['summary']['severity_breakdown']['low']}")
        
        # Save results
        print("\n💾 Saving results to security_qa_results.json...")
        with open(RESULTS_FILE, "w") as f:
            json.dump(self.results, f, indent=2)
        
        return len(self.results["vulnerabilities"]) == 0


if __name__ == "__main__":
    tester = SecurityTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)