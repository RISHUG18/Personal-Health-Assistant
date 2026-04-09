"""Script to create a test user through the auth registration flow."""
import requests

# User data
user_data = {
    "email": "test.patient@vitalis.health",
    "password": "TestPatient123!",
    "full_name": "Arjun Sharma",
    "date_of_birth": "1990-01-15",
    "height_cm": 175.0,
    "weight_kg": 70.0,
    "role": "patient",
}

# Create user through the canonical auth flow
response = requests.post(
    "http://127.0.0.1:8000/auth/register",
    json=user_data,
    headers={"Content-Type": "application/json"}
)

if response.status_code == 201:
    payload = response.json()
    print("User created successfully!")
    print(f"\nUser ID: {payload['user_id']}")
    print(f"Name: {user_data['full_name']}")
    print(f"Email: {user_data['email']}")
    print(f"\nUpdate your Android app to use this user ID:")
    print(f'val userId = "{payload["user_id"]}"')
elif response.status_code == 400:
    print("Registration failed. The user may already exist or the payload may be invalid.")
    print("Use an existing login or change the email before retrying.")
    print(response.text)
else:
    print(f"Error creating user: {response.status_code}")
    print(response.text)
