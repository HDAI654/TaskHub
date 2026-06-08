import logging
from workers.celery_app import celery_app
from workers.conf import Config

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, name="send_email")
def send_email_task(self, to_email: str, subject: str, body: str) -> dict:
    """
    Send an email to the user.

    In production, this would connect to SMTP server.
    For now, just log the email.
    """
    logger.info("=" * 50)
    logger.info("📧 EMAIL WOULD BE SENT (in production)")
    logger.info(f"   To:      {to_email}")
    logger.info(f"   Subject: {subject}")
    logger.info(f"   Body:    {body[:200]}...")
    logger.info("=" * 50)

    # Uncomment for real email sending:
    # try:
    #     import smtplib
    #     from email.mime.text import MIMEText
    #     msg = MIMEText(body)
    #     msg["Subject"] = subject
    #     msg["From"] = "noreply@taskhub.com"
    #     msg["To"] = to_email
    #
    #     with smtplib.SMTP("smtp.gmail.com", 587) as server:
    #         server.starttls()
    #         server.login("user@gmail.com", "password")
    #         server.send_message(msg)
    # except Exception as e:
    #     logger.error(f"Failed to send email: {e}")
    #     self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

    return {"status": "sent", "to": to_email, "subject": subject}


@celery_app.task(name="send_password_reset_email")
def send_password_reset_email(
    to_email: str, token: str, expires_in_minutes: int = 15
) -> dict:
    """Send password reset email with reset link"""
    reset_link = f"{Config.RESET_PASSWORD_URL}?token={token}"

    subject = "Password Reset Request"
    body = f"""
    Hello,
    
    You requested a password reset for your TaskHub account.
    
    Click the link below to reset your password (valid for {expires_in_minutes} minutes):
    
    {reset_link}
    
    If you didn't request this, please ignore this email.
    
    Best regards,
    TaskHub Team
    """
    return send_email_task(to_email, subject, body.strip())
