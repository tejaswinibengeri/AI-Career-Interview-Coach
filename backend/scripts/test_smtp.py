"""
Utility script to test sending a real email via configured SMTP settings.
Usage: python scripts/test_smtp.py [recipient_email]
"""

import asyncio
import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.services.email_service import send_email

async def main():
    recipient = sys.argv[1] if len(sys.argv) > 1 else "sandeepgudasi3@gmail.com"
    print("=" * 60)
    print("SMTP Configuration Test")
    print("=" * 60)
    print(f"SMTP_ENABLED   : {settings.SMTP_ENABLED}")
    print(f"SMTP_HOST      : {settings.SMTP_HOST}")
    print(f"SMTP_PORT      : {settings.SMTP_PORT}")
    print(f"SMTP_USER      : {settings.SMTP_USER}")
    print(f"SMTP_FROM_NAME : {settings.SMTP_FROM_NAME}")
    print(f"Recipient      : {recipient}")
    print("=" * 60)

    if "mailtrap" in settings.SMTP_HOST.lower():
        print("\n⚠️ WARNING: Your SMTP_HOST is currently pointing to 'sandbox.smtp.mailtrap.io'.")
        print("Mailtrap Sandbox NEVER delivers emails to real Gmail inboxes.")
        print("To deliver emails to your real Gmail, you need to use Google's SMTP:")
        print("  SMTP_HOST=smtp.gmail.com")
        print("  SMTP_PORT=587")
        print("  SMTP_USER=<your_gmail_address@gmail.com>")
        print("  SMTP_PASSWORD=<your_16_character_google_app_password>")
        print("=" * 60)

    print("\nAttempting to send a test email...")
    subject = "🎯 CareerCoachAI — SMTP Verification Test"
    html = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px; background-color: #0f172a; color: #ffffff; border-radius: 12px;">
        <h2 style="color: #6366f1;">✅ Gmail SMTP Connection Verified!</h2>
        <p>This is a test notification from your <strong>Placement AI Platform</strong>.</p>
        <p>Your SMTP email delivery is now successfully connected to your real Gmail inbox!</p>
        <hr style="border: 0; border-top: 1px solid #334155; margin: 20px 0;">
        <small style="color: #94a3b8;">Sent to {recipient}</small>
    </div>
    """

    success = await send_email(recipient, subject, html)
    if success:
        print("\n✅ SUCCESS: Email was sent successfully!")
        if "mailtrap" in settings.SMTP_HOST.lower():
            print("Note: Since host is Mailtrap, view it at https://mailtrap.io/inboxes")
        else:
            print(f"Check your inbox at: {recipient}")
    else:
        print("\n❌ FAILED: Could not send email. Check error logs above.")

if __name__ == "__main__":
    asyncio.run(main())
