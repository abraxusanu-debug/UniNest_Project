import smtplib
from email.message import EmailMessage

from flask import has_request_context, request

from app.models import SiteSettings
from app.services.errors import ServiceError


def _account_url(path):
    from config import Config

    base_url = getattr(Config, "PUBLIC_BASE_URL", "")
    if not base_url and has_request_context():
        base_url = request.host_url.rstrip("/")
    if not base_url:
        return path
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


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

    server = smtplib.SMTP(settings.smtp_server, settings.smtp_port or 587, timeout=10)
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
    link = _account_url(f"verify-email/{user.verification_token}")
    body = (
        f"Hi {user.full_name},\n\n"
        "Please verify your email address for UniNest before you continue.\n\n"
        f"Verification link: {link}\n"
    )
    send_email("Verify your UniNest email", body, user.email)
    return True


def send_account_created_email(user):
    link = _account_url("login")
    body = (
        f"Hi {user.full_name},\n\n"
        "Your UniNest account was created successfully.\n"
        "For security, do not share your password or verification links.\n\n"
        f"Open UniNest: {link}\n"
    )
    send_email("Welcome to UniNest", body, user.email)
    return True


def send_password_reset_email(user):
    if not getattr(user, "reset_token", None):
        return False
    link = _account_url(f"reset-password/{user.reset_token}")
    body = (
        f"Hi {user.full_name},\n\n"
        "You requested a password reset for your UniNest account.\n"
        "If you did not request this, ignore this email and contact the hostel office.\n\n"
        f"Reset link: {link}\n"
    )
    send_email("Reset your UniNest password", body, user.email)
    return True


def send_login_alert_email(user):
    link = _account_url("dashboard")
    body = (
        f"Hi {user.full_name},\n\n"
        "A successful login was made to your UniNest account.\n"
        "If this was not you, reset your password immediately.\n\n"
        f"Open UniNest: {link}\n"
    )
    send_email("UniNest login alert", body, user.email)
    return True


def send_notification_email(user, title):
    link = _account_url("dashboard")
    body = (
        f"Hi {user.full_name},\n\n"
        f"You have a new UniNest update: {title}.\n"
        "Sign in to view the appropriate status and details in your account.\n"
        "This email does not contain payment, personal, or other sensitive details.\n\n"
        f"Open UniNest: {link}\n"
    )
    send_email(f"UniNest update: {title}", body, user.email)
    return True
