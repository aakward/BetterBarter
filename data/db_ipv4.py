from supabase import create_client, Client
import streamlit as st

# Get Supabase credentials from Streamlit secrets
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_ANON_KEY = st.secrets["SUPABASE_ANON_KEY"]
SUPABASE_SERVICE_ROLE_KEY=st.secrets["SUPABASE_SERVICE_ROLE_KEY"]

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise RuntimeError("Supabase credentials are missing in Streamlit secrets.")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

def get_db():
    """
    Instead of returning a raw SQLAlchemy session,
    this returns the Supabase client.
    """
    return supabase