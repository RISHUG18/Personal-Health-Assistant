import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
anon_key = os.getenv("SUPABASE_ANON_KEY")

# Create two clients: One for Admin overrides, one for normal login
admin_supabase = create_client(url, service_key)
auth_supabase = create_client(url, anon_key)

# ── YOUR TARGET ──────────────────────────────────────────────────
TARGET_UUID = "1bfe631d-f2bb-43a1-91f3-2d413cd4c5e8"
TEMP_PASSWORD = "SuperSecurePassword123!"
# ─────────────────────────────────────────────────────────────────

try:
    print(f"1. Fetching profile for {TARGET_UUID}...")
    user_data = admin_supabase.auth.admin.get_user_by_id(TARGET_UUID)
    user_email = user_data.user.email
    print(f"   Found user: {user_email}")

    print("2. Forcing password reset via Admin override...")
    admin_supabase.auth.admin.update_user_by_id(
        TARGET_UUID,
        {"password": TEMP_PASSWORD}
    )

    print("3. Logging in to generate fresh JWT...")
    response = auth_supabase.auth.sign_in_with_password({
        "email": user_email,
        "password": TEMP_PASSWORD
    })

    print("\n=== SUCCESS ===")
    print("Copy this JWT and paste it into the Swagger 🔒 Authorization box:\n")
    print(response.session.access_token)

except Exception as e:
    print("\nImpersonation failed:", e)