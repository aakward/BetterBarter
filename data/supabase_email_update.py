from supabase import create_client
import streamlit as st

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = st.secrets["SUPABASE_SERVICE_ROLE_KEY"]  # service_role key

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def sync_emails_to_profiles():
    # Fetch all users from Supabase Auth
    result = supabase.auth.admin.list_users()
    
    # Depending on version, result may have 'users' attribute or be a list
    users = getattr(result, "users", result)

    for user in users:
        user_id = user.id       # <- Use attribute access
        email = user.email

        if email:
            # Update profiles table
            res = supabase.table("profiles").update({"email": email}).eq("id", user_id).execute()
            print(f"Updated {user_id} → {email}")
        else:
            print(f"No email found for user {user_id}")

if __name__ == "__main__":
    sync_emails_to_profiles()