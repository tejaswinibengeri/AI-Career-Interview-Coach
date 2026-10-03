"""
Simple email sender for job match reminders.
No n8n or external automation tool needed — just call send_job_match_email()
directly from wherever your job-matching logic detects a new match.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- Mailtrap sandbox credentials (for TESTING) ---
# Swap these for a real provider (Gmail, SendGrid, etc.) when going to production.
SMTP_HOST = "sandbox.smtp.mailtrap.io"
SMTP_PORT = 587
SMTP_USER = "977a6e0a7d13df"       # your Mailtrap username
SMTP_PASSWORD = "YOUR_MAILTRAP_PASSWORD"  # paste the real password here


def send_job_match_email(to_email: str, job_title: str, company: str, job_url: str = ""):
    """
    Sends a simple reminder email about a new job match.
    """
    subject = f"New Job Match: {job_title} at {company}"
    body = f"""
    <p>Hi,</p>
    <p>We found a new job match for you:</p>
    <p><b>{job_title}</b> at <b>{company}</b></p>
    {f'<p><a href="{job_url}">View job posting</a></p>' if job_url else ""}
    <p>— CareerCoachAI</p>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = "noreply@careercoachai.com"
    msg["To"] = to_email
    msg.attach(MIMEText(body, "html"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()  # required for port 587
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(msg["From"], [to_email], msg.as_string())

    print(f"Reminder email sent to {to_email}")


# Example usage — call this wherever your job matching logic finds a new match:
if __name__ == "__main__":
    send_job_match_email(
        to_email="recipient@test.com",
        job_title="Backend Developer",
        company="Acme Corp",
        job_url="https://example.com/job/123",
    )
