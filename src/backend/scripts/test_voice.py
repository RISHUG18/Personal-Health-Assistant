import requests
import sys
import os

URL = "http://localhost:8000/voice/voice_chat"
DEFAULT_USER_ID = "aaaaaaaa-0001-0001-0001-000000000001"


def resolve_user_id() -> str:
    """Return a valid UUID for voice endpoint tests."""
    user_id = os.getenv("VOICE_TEST_USER_ID", DEFAULT_USER_ID).strip()
    return user_id or DEFAULT_USER_ID

def test_text_input():
    print("Testing TEXT input...")
    payload = {
        "text": "Hello, this is a test from the script.",
        "user_id": resolve_user_id(),
        # Keep smoke tests independent from retrieval setup.
        "use_rag": False,
    }
    try:
        response = requests.post(URL, json=payload, timeout=5)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            transcript = data.get("transcript")
            response_text = data.get("response_text")
            
            print(f"Transcript: {transcript}")
            print(f"Response: {response_text}")
            
            if transcript and response_text:
                print("✅ TEXT input test SUCCESSFUL.")
            else:
                print("❌ Missing fields in response.")
        elif response.status_code == 404:
            print("❌ Endpoint not found. Ensure FastAPI is running on port 8000.")
            sys.exit(1)
        else:
            print(f"❌ TEXT input test FAILED: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the server. Is FastAPI running on port 8000?")
        sys.exit(1)
        
def test_no_input():
    print("\nTesting INVALID input (No data)...")
    try:
        response = requests.post(URL, json={}, timeout=5)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 400:
            print("✅ INVALID input test SUCCESSFUL (properly rejected).")
        else:
            print(f"❌ INVALID input test FAILED: Expected 400, got {response.status_code}")
    except requests.exceptions.RequestException as e:
         print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    print(f"Running tests against {URL}\n")
    print(f"Using user_id={resolve_user_id()} (override with VOICE_TEST_USER_ID)")
    test_text_input()
    test_no_input()