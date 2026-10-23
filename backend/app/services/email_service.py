import smtplib
from email.message import EmailMessage

from app.models import SiteSettings
from app.services.errors import ServiceError


def send_email(subject, body, recipient_email, *, html_body=None):
    settings = SiteSettings.get_or_create()
    if not settings.site_email or not settings.site_email_password:
        raise ServiceError("site email settings are not configured")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = f"{settings.sender_name} <{settings.site_email}>"
    message["To"] = recipient_email
    if html_body:
        message.set_content(body)
        message.add_alternative(html_body, subtype="html")
    else:
        message.set_content(body)

    server = smtplib.SMTP(settings.smtp_server, settings.smtp_port or 587)
    try:
        if settings.use_tls:
            server.starttls()
        server.login(settings.site_email, settings.site_email_password)
        server.send_message(message)
    finally:
        server.quit()

    return True


def send_verification_email(user):
    if not getattr(user, "verification_token", None):
        return False
    link = f"/verify-email/{user.verification_token}"
    body = (
        f"Hi {user.full_name},\n\n"
        "Please verify your email address for UniNest before you continue.\n\n"
        f"Verification link: {link}\n"
    )
    send_email("Verify your UniNest email", body, user.email)
    return True


def send_password_reset_email(user):
    if not getattr(user, "reset_token", None):
        return False
    link = f"/reset-password/{user.reset_token}"
    body = (
        f"Hi {user.full_name},\n\n"
        "You requested a password reset for your UniNest account.\n\n"
        f"Reset link: {link}\n"
    )
    send_email("Reset your UniNest password", body, user.email)
    return True
