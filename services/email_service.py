# services/email_service.py
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import streamlit as st

SENDGRID_API_KEY = st.secrets["SENDGRID_API_KEY"]
FROM_EMAIL = st.secrets["FROM_EMAIL"]

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
    except Exception as e:
        print(f"Error sending email to {to_email}: {e}")

def send_match_request_email(receiver, sender):
    subject = "New match request waiting for your response on BetterBarter!"
    html_content = f"""
    Hi {receiver.name},<br><br>
    {sender.name} has sent you a match request on BetterBarter.<br>
    Log in to your account to review and respond.<br><br>
    Happy helping! :)
    """
    send_email(receiver.email, subject, html_content)

def send_match_accepted_email(user1, user2):
    subject = "Your match request was accepted!"
    html_content_user1 = f"""
    Hi {user1.name},<br><br>
    Good news! Your match with {user2.name} has been accepted.<br>
    Contact Info:<br>
    Email: {user2.email}<br>
    Phone: {user2.phone or 'Not provided'}<br><br>
    Happy trading!
    """
    html_content_user2 = f"""
    Hi {user2.name},<br><br>
    Good news! Your match with {user1.name} has been accepted.<br>
    Contact Info:<br>
    Email: {user1.email}<br>
    Phone: {user1.phone or 'Not provided'}<br><br>
    Happy trading!
    """
    send_email(user1.email, subject, html_content_user1)
    send_email(user2.email, subject, html_content_user2)
