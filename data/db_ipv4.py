from supabase import create_client, Client
import streamlit as st

# Get Supabase credentials from Streamlit secrets
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_ANON_KEY = st.secrets["SUPABASE_ANON_KEY"]

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise RuntimeError("Supabase credentials are missing in Streamlit secrets.")


def get_db() -> Client:
    """
    Returns a Supabase client bound to the current user's session.
    Each call creates a new client so sessions are not shared between users.
    """
    client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

    # Rehydrate the user's session if it exists in st.session_state
    if "supabase_session" in st.session_state:
        session = st.session_state["supabase_session"]
        try:
            client.auth.set_session(
                session["access_token"],
                session["refresh_token"],
            )
        except Exception as e:
            st.warning(f"Could not restore Supabase session: {e}")

    return client
