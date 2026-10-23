from dotenv import load_dotenv
from app.notifications import send_incident_email

load_dotenv()

success = send_incident_email(
    subject="[CloudPulse] Test Notification",
    body=(
        "Hello!\n\n"
        "This is a test incident notification from CloudPulse.\n"
        "If you received this email, SMTP configuration is working."
    ),
)

if success:
    print("SUCCESS: Email sent. Check your inbox.")
else:
    print("FAILED: Check your terminal logs and .env settings.")