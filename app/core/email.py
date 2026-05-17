import smtplib
from email.message import EmailMessage

from app.core.config import settings


def send_email(to_email: str, subject: str, body: str) -> None:
    if not settings.smtp_host:
        print("\n".join(["[email disabled]", f"to: {to_email}", f"subject: {subject}", body]))
        return

    message = EmailMessage()
    message["From"] = settings.smtp_from_email
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
        if settings.smtp_use_tls:
            smtp.starttls()
        if settings.smtp_username and settings.smtp_password:
            smtp.login(settings.smtp_username, settings.smtp_password)
        smtp.send_message(message)


def notify_admin(subject: str, body: str) -> None:
    admin_email = settings.admin_notification_email or settings.first_admin_email
    if admin_email:
        send_email(admin_email, subject, body)
