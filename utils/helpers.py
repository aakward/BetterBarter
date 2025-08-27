import streamlit as st
import bcrypt
import hashlib


def rerun():
    st.session_state["rerun_flag"] = not st.session_state.get("rerun_flag", False)


def hash_password(password: str) -> str:
    """Hash a plain-text password."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(password: str, hashed: str) -> bool:
    """Verify a plain-text password against the stored hash."""
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

def hash_phone(phone: str) -> str:
    """Hash a phone number using SHA-256 for anonymization."""
    return hashlib.sha256(phone.encode("utf-8")).hexdigest()