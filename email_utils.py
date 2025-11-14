import os
import requests

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL", "no-reply@yourdomain.com")  # Use a verified sender at SendGrid!

def send_email(to_email: str, subject: str, html_body: str):
    if not SENDGRID_API_KEY:
        print("SendGrid API key missing. Not sending email.")
        return
    data = {
        "personalizations": [
            { "to": [ { "email": to_email } ] }
        ],
        "from": { "email": FROM_EMAIL },
        "subject": subject,
        "content": [ { "type": "text/html", "value": html_body } ],
    }
    response = requests.post(
        "https://api.sendgrid.com/v3/mail/send",
        headers={
            "Authorization": f"Bearer {SENDGRID_API_KEY}",
            "Content-Type": "application/json"
        },
        json=data
    )
    if response.status_code != 202:
        print("Email failed:", response.text)
