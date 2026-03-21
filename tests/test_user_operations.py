"""Integration tests for user schema CRUD operations."""
import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestUserOperations:
    """Test all user-related CRUD operations."""

    def test_create_user_success(self, test_client: TestClient, test_user_id: str):
        """Test creating a new user with valid data."""
        user_data = {
            "email": f"newuser_{test_user_id[:8]}@example.com",
            "full_name": "John Doe",
            "phone": "+919876543210",
            "date_of_birth": "1995-06-15",
            "gender": "male",
            "address_line1": "123 Main Street",
            "city": "Mumbai",
            "state": "Maharashtra",
            "postal_code": "400001",
            "country": "India",
            "blood_group": "A+",
            "height_cm": 180,
            "weight_kg": 75
        }

        response = test_client.post("/api/v1/users", json=user_data)

        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        user = response.json()
        assert user["email"] == user_data["email"]
        assert user["full_name"] == user_data["full_name"]
        assert user["blood_group"] == user_data["blood_group"]
        assert "id" in user
        assert user["is_active"] is True

    def test_create_user_duplicate_email(self, test_client: TestClient, test_user: dict):
        """Test that creating a user with duplicate email fails."""
        user_data = {
            "email": test_user["email"],  # Use existing user's email
            "full_name": "Duplicate User"
        }

        response = test_client.post("/api/v1/users", json=user_data)

        assert response.status_code == 409, f"Expected 409 for duplicate email, got {response.status_code}"
        assert "already exists" in response.text.lower()

    def test_create_user_invalid_email(self, test_client: TestClient):
        """Test that creating a user with invalid email fails."""
        user_data = {
            "email": "not-an-email",
            "full_name": "Invalid Email User"
        }

        response = test_client.post("/api/v1/users", json=user_data)

        assert response.status_code == 422, f"Expected 422 for invalid email, got {response.status_code}"

    def test_get_user_by_id(self, test_client: TestClient, test_user: dict):
        """Test retrieving a user by their ID."""
        user_id = test_user["id"]

        response = test_client.get(f"/api/v1/users/{user_id}")

        assert response.status_code == 200
        user = response.json()
        assert user["id"] == user_id
        assert user["email"] == test_user["email"]
        assert user["full_name"] == test_user["full_name"]

    def test_get_user_not_found(self, test_client: TestClient):
        """Test retrieving a non-existent user."""
        fake_id = "00000000-0000-0000-0000-000000000000"

        response = test_client.get(f"/api/v1/users/{fake_id}")

        assert response.status_code == 404

    def test_get_user_by_email(self, test_client: TestClient, test_user: dict):
        """Test retrieving a user by their email."""
        email = test_user["email"]

        response = test_client.get(f"/api/v1/users/email/{email}")

        assert response.status_code == 200
        user = response.json()
        assert user["email"] == email
        assert user["id"] == test_user["id"]

    def test_update_user_success(self, test_client: TestClient, test_user: dict):
        """Test updating user information."""
        user_id = test_user["id"]
        update_data = {
            "full_name": "Updated Name",
            "phone": "+919999999999",
            "weight_kg": 72.5
        }

        response = test_client.patch(f"/api/v1/users/{user_id}", json=update_data)

        assert response.status_code == 200
        updated_user = response.json()
        assert updated_user["full_name"] == update_data["full_name"]
        assert updated_user["phone"] == update_data["phone"]
        assert updated_user["weight_kg"] == update_data["weight_kg"]
        # Unchanged fields should remain the same
        assert updated_user["email"] == test_user["email"]

    def test_update_user_invalid_blood_group(self, test_client: TestClient, test_user: dict):
        """Test that updating with invalid blood group fails."""
        user_id = test_user["id"]
        update_data = {"blood_group": "Z+"}  # Invalid blood group

        response = test_client.patch(f"/api/v1/users/{user_id}", json=update_data)

        # Should fail validation (422) or ignore invalid value
        assert response.status_code in [422, 400]

    def test_delete_user_success(self, test_client: TestClient, test_user_id: str):
        """Test deleting a user."""
        # Create a user specifically for deletion
        user_data = {
            "email": f"delete_{test_user_id[:8]}@example.com",
            "full_name": "User To Delete"
        }
        create_response = test_client.post("/api/v1/users", json=user_data)
        assert create_response.status_code == 201
        user_id = create_response.json()["id"]

        # Delete the user
        delete_response = test_client.delete(f"/api/v1/users/{user_id}")
        assert delete_response.status_code == 200

        # Verify user is deleted
        get_response = test_client.get(f"/api/v1/users/{user_id}")
        assert get_response.status_code == 404

    def test_user_with_minimal_data(self, test_client: TestClient, test_user_id: str):
        """Test creating a user with only required fields."""
        user_data = {
            "email": f"minimal_{test_user_id[:8]}@example.com",
            "full_name": "Minimal User"
        }

        response = test_client.post("/api/v1/users", json=user_data)

        assert response.status_code == 201
        user = response.json()
        assert user["email"] == user_data["email"]
        assert user["full_name"] == user_data["full_name"]
        # Optional fields should be null or have defaults
        assert user.get("phone") is None
        assert user.get("date_of_birth") is None
