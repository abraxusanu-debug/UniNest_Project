from app.extensions import db
from app.models import Notification, User


def notify(user_id, type, title, message, is_read=False):
    notification = Notification(
        user_id=user_id,
        type=type,
        title=title,
        message=message,
        is_read=is_read,
    )
    db.session.add(notification)

    user = db.session.get(User, user_id)
    if user and user.is_active and user.email:
        try:
            from app.services.email_service import send_notification_email

            send_notification_email(user, title)
        except Exception:
            # In-app notifications remain available when SMTP is unconfigured or temporarily offline.
            pass
