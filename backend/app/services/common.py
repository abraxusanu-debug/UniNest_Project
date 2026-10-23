from app.extensions import db
from app.models import Notification


def notify(user_id, type, title, message, is_read=False):
    db.session.add(Notification(user_id=user_id, type=type, title=title, message=message, is_read=is_read))
