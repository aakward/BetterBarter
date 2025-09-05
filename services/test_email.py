from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import streamlit as st
import os, certifi

# Force Python to use certifi's trusted CA bundle
os.environ["SSL_CERT_FILE"] = certifi.where()

SENDGRID_API_KEY = st.secrets["SENDGRID_API_KEY"]
FROM_EMAIL = "no-reply@betterbarter.nl"  # must be the same one you verified in SendGrid

def send_test_email():
    message = Mail(
        from_email=FROM_EMAIL,
        to_emails="aakashbanik@gmail.com",  # send to yourself
        subject="SendGrid Test Email",
        html_content="<strong>If you received this, SendGrid is working!</strong>"
    )
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.body}")
        print(f"Response Headers: {response.headers}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    send_test_email()
