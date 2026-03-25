"""Script to create a test user in the database."""
import requests
import json

# User data
user_data = {
    "email": "test.patient@vitalis.health",
    "full_name": "Arjun Sharma",
    "phone": "+91-9876543210",
    "date_of_birth": "1990-01-15",
    "gender": "male",
    "city": "Hyderabad",
    "state": "Telangana",
    "country": "India",
    "blood_group": "O+",
    "height_cm": 175.0,
    "weight_kg": 70.0
}

# Create user
response = requests.post(
    "http://127.0.0.1:8000/api/v1/users",
    json=user_data,
    headers={"Content-Type": "application/json"}
)

if response.status_code == 201:
    user = response.json()
    print("User created successfully!")
    print(f"\nUser ID: {user['id']}")
    print(f"Name: {user['full_name']}")
    print(f"Email: {user['email']}")
    print(f"\nUpdate your Android app to use this user ID:")
    print(f'val userId = "{user["id"]}"')
elif response.status_code == 409:
    print("User with this email already exists.")
    print("Fetching existing user...")

    # Get user by email
    email = user_data["email"]
    get_response = requests.get(f"http://127.0.0.1:8000/api/v1/users/email/{email}")

    if get_response.status_code == 200:
        user = get_response.json()
        print(f"\nExisting user found!")
        print(f"User ID: {user['id']}")
        print(f"Name: {user['full_name']}")
        print(f"Email: {user['email']}")
        print(f"\nUpdate your Android app to use this user ID:")
        print(f'val userId = "{user["id"]}"')
else:
    print(f"Error creating user: {response.status_code}")
    print(response.text)
