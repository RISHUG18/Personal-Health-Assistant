import sys
from pathlib import Path

# Add src/ to sys.path so 'backend' can be imported
_SRC_DIR = Path(__file__).resolve().parents[2]
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from backend.main import app

class TestAuthEndpoints(unittest.TestCase):
    """Test suite covering the authentication and protected route functionalities."""
    
    def setUp(self):
        self.client = TestClient(app)

    @patch("backend.routes.auth.get_supabase_client")
    def test_register_success(self, mock_get_client):
        # Mocking Supabase Client
        mock_supabase = MagicMock()
        mock_get_client.return_value = mock_supabase
        
        # Mock admin.create_user response
        mock_user = MagicMock()
        mock_user.id = "12345678-1234-5678-1234-567812345678"
        mock_user_resp = MagicMock()
        mock_user_resp.user = mock_user
        mock_supabase.auth.admin.create_user.return_value = mock_user_resp
        
        # Mock immediate sign-in response
        mock_session = MagicMock()
        mock_session.access_token = "fake-access-token"
        mock_session.refresh_token = "fake-refresh-token"
        mock_auth_resp = MagicMock()
        mock_auth_resp.session = mock_session
        mock_supabase.auth.sign_in_with_password.return_value = mock_auth_resp
        
        response = self.client.post("/auth/register", json={
            "email": "test@example.com",
            "password": "password123",
            "full_name": "Test User",
            "role": "patient"
        })
        
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["user_id"], mock_user.id)
        self.assertEqual(data["access_token"], "fake-access-token")
        
        mock_supabase.auth.admin.create_user.assert_called_once()
        mock_supabase.auth.sign_in_with_password.assert_called_once()
        mock_supabase.table.assert_called_with("users")
        mock_supabase.table.return_value.insert.assert_called_once()

    @patch("backend.routes.auth.get_supabase_client")
    def test_register_invalid_role(self, mock_get_client):
        response = self.client.post("/auth/register", json={
            "email": "test@example.com",
            "password": "password123",
            "full_name": "Test User",
            "role": "admin"  # Invalid role
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("Role must be either", response.json()["detail"])

    @patch("backend.routes.auth.get_supabase_client")
    def test_login_success(self, mock_get_client):
        mock_supabase = MagicMock()
        mock_get_client.return_value = mock_supabase
        
        mock_user = MagicMock()
        mock_user.id = "12345678-1234-5678-1234-567812345678"
        mock_session = MagicMock()
        mock_session.access_token = "fake-access-token"
        mock_session.refresh_token = "fake-refresh-token"
        
        mock_auth_resp = MagicMock()
        mock_auth_resp.user = mock_user
        mock_auth_resp.session = mock_session
        mock_supabase.auth.sign_in_with_password.return_value = mock_auth_resp
        
        # Mock DB update for last_login_at
        mock_supabase.table().update().eq().execute.return_value = MagicMock()
        
        response = self.client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "password123"
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["user_id"], mock_user.id)
        self.assertEqual(data["access_token"], "fake-access-token")
        
        mock_supabase.auth.sign_in_with_password.assert_called_once()
        mock_supabase.table.assert_called_with("users")

    @patch("backend.routes.auth.get_supabase_client")
    def test_login_failure(self, mock_get_client):
        mock_supabase = MagicMock()
        mock_get_client.return_value = mock_supabase
        mock_supabase.auth.sign_in_with_password.side_effect = Exception("Invalid login credentials")
        
        response = self.client.post("/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrong"
        })
        
        self.assertEqual(response.status_code, 401)
        self.assertIn("Invalid login credentials", response.json()["detail"])

    def test_protected_upload_missing_token(self):
        # /upload/report requires a token, if not present FastAPI HTTPBearer returns 403
        response = self.client.post("/upload/report", files={"file": ("test.pdf", b"%PDF-1.4", "application/pdf")})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"], "Not authenticated")

    @patch("backend.middleware.auth_middleware.get_supabase_client")
    def test_protected_upload_invalid_token(self, mock_get_client):
        mock_supabase = MagicMock()
        mock_get_client.return_value = mock_supabase
        
        # Simulate invalid token thrown by Supabase get_user natively
        mock_supabase.auth.get_user.side_effect = Exception("Invalid JWT signature")
        
        response = self.client.post(
            "/upload/report", 
            files={"file": ("test.pdf", b"%PDF-1.4", "application/pdf")},
            headers={"Authorization": "Bearer bad-token"}
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Invalid authentication credentials: Invalid JWT signature")

if __name__ == "__main__":
    unittest.main()
