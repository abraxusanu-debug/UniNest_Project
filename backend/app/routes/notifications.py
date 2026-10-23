from flask import Blueprint, jsonify

from app.extensions import db
from app.models import Notification
from app.utils import get_current_user

bp = Blueprint("notifications", __name__, url_prefix="/api/notifications")


@bp.get("")
def my_notifications():
    user = get_current_user()
    items = Notification.query.filter_by(user_id=user.id).order_by(Notification.created_at.desc()).all()
    unread = sum(1 for n in items if not n.is_read)
    return jsonify({"notifications": [n.to_dict() for n in items], "count": len(items), "unread": unread})


@bp.post("/<int:notification_id>/read")
def mark_read(notification_id):
    user = get_current_user()
    notification = db.session.get(Notification, notification_id)
    if not notification or notification.user_id != user.id:
        return jsonify({"error": "not_found", "message": "notification not found"}), 404
    notification.is_read = True
    db.session.commit()
    return jsonify(notification.to_dict())


@bp.post("/read-all")
def mark_all_read():
    user = get_current_user()
    Notification.query.filter_by(user_id=user.id, is_read=False).update({"is_read": True})
    db.session.commit()
    return jsonify({"message": "all notifications marked as read"})
