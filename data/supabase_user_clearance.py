from supabase import create_client
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

url = os.getenv("SUPABASE_URL")
service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # must be service role

supabase = create_client(url, service_role_key)

# List all users
users = supabase.auth.admin.list_users()  # returns a list of User objects

print(f"Found {len(users)} users. Deleting them now...")

# Delete each user
for user in users:
    user_id = user.id
    supabase.auth.admin.delete_user(user_id)
    print(f"Deleted user {user.email} ({user_id})")

print("All users deleted successfully.")
