from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import socket
import streamlit as st

Base = declarative_base()

# Force IPv4 for Streamlit Cloud (avoids IPv6 connection issue)
original_getaddrinfo = socket.getaddrinfo
def getaddrinfo_ipv4(*args, **kwargs):
    results = original_getaddrinfo(*args, **kwargs)
    return [r for r in results if r[0] == socket.AF_INET]
socket.getaddrinfo = getaddrinfo_ipv4

# Get database URL from Streamlit secrets
DATABASE_URL = st.secrets["SUPABASE_DB_URL"]
if not DATABASE_URL:
    raise RuntimeError("SUPABASE_DB_URL is not set. Check your Streamlit secrets file.")

# Ensure SSL is required for Supabase
if "sslmode=" not in DATABASE_URL:
    if "?" in DATABASE_URL:
        DATABASE_URL += "&sslmode=require"
    else:
        DATABASE_URL += "?sslmode=require"

print(f"Connecting to database at {DATABASE_URL}")

engine = create_engine(DATABASE_URL, echo=True, future=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
