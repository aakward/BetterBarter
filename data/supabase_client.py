import os
from supabase import create_client, Client

url = os.getenv("SUPABASE_URL")
anon_key = os.getenv("SUPABASE_ANON_KEY")

supabase: Client = create_client(url, anon_key)
