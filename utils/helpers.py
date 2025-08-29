import streamlit as st
import bcrypt
import hashlib
import smtplib
from email.message import EmailMessage

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


def send_match_email(to_email: str, from_name: str, offer_title: str, request_title: str, custom_message: str = None):
    """
    Send an email notifying the offer owner of a new match request.
    Optionally include a custom message from the requester.
    """
    msg = EmailMessage()
    msg['Subject'] = f"New match request: {offer_title}"
    msg['From'] = "noreply@barterapp.com"
    msg['To'] = to_email

    body = f"{from_name} is interested in your offer '{offer_title}' matching request '{request_title}'."
    if custom_message:
        body += f"\n\nMessage from requester:\n{custom_message}"

    msg.set_content(body)

    with smtplib.SMTP('smtp.your-email.com', 587) as server:
        server.starttls()
        server.login("your-email@domain.com", "your-password")
        server.send_message(msg)