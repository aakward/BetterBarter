# services/email_service.py
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import ssl, certifi, os

# Force Python to use certifi’s CA bundle
os.environ["SSL_CERT_FILE"] = certifi.where()

SENDGRID_API_KEY = None
FROM_EMAIL = None

# Try env vars first, fallback to st.secrets
try:
    import streamlit as st
    SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")
    FROM_EMAIL = os.environ.get("FROM_EMAIL")
except Exception:
    SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
    FROM_EMAIL = os.getenv("FROM_EMAIL")


def send_email(to_email, subject, html_content):
    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=to_email,
        subject=subject,
        html_content=html_content
    )
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        print(f"Email sent to {to_email}: {response.status_code}")
        return True
    except Exception as e:
        print(f"Error sending email to {to_email}: {e}")
        return False


def format_contact_info(profile, contact=None):
    """
    Returns formatted contact info for email or UI display.
    - contact: dict with 'mode' and 'value' (preferred contact)
    - profile: user profile object with 'share_phone' and 'phone'
    """
    lines = []

    if contact and contact.get("mode") and contact.get("value"):
        lines.append(f"{contact['mode']}: {contact['value']} (preferred)")
    if profile.share_phone and profile.phone:
        lines.append(f"Phone (from profile): {profile.phone}")
    if not lines:
        lines.append(f"Email: {profile.email}")
    return "<br>".join(lines)


def send_match_request_email(receiver, sender):
    """
    Notify receiver that someone sent them a match request.
    No contact details are shared at this stage.
    """
    subject = "New match request waiting for your response on BetterBarter!"
    html_content = f"""
    Hi {receiver.name},<br><br>
    {sender.name} has sent you a match request on BetterBarter at betterbarter.streamlit.app <br>
    Log in to your account to review and respond.<br><br>
    Happy helping! :)
    """
    send_email(receiver.email, subject, html_content)


def send_match_accepted_email(user1, user2, user1_contact=None, user2_contact=None):
    """
    Send email to both users when a match is accepted.
    Contact details are exchanged at this stage.
    """
    subject = "Your match request was accepted on BetterBarter!"

    html_content_user1 = f"""
    Hi {user1.name},<br><br>
    Good news! Your match with {user2.name} has been accepted.<br>
    Contact Info to reach {user2.name}:<br>
    {format_contact_info(user2, user2_contact)}<br><br>
    Please feel free to contact {user2.name}.<br><br>
    Happy helping!
    """

    html_content_user2 = f"""
    Hi {user2.name},<br><br>
    Good news! Your match with {user1.name} has been accepted.<br>
    Contact Info to reach {user1.name}:<br>
    {format_contact_info(user1, user1_contact)}<br><br>
    Please feel free to contact {user1.name}.<br><br>
    Happy helping!
    """

    send_email(user1.email, subject, html_content_user1)
    send_email(user2.email, subject, html_content_user2)
