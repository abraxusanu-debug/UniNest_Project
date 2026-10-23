from datetime import datetime
from typing import Optional

from app.extensions import db
from app.models import Application, Hostel
from app.services.errors import Conflict, Forbidden, NotFound
from app.services.common import notify

VALID_ROOM_PREFS = ("any", "single", "shared")
ACTIVE_STATUSES = ("pending", "under_review", "approved", "allocated")


def create_application(student, room_preference="any", notes=None, preferred_hostel_id=None):
    if student.verification_status != "verified":
        raise Forbidden("your account must be verified before applying")

    active = Application.query.filter(
        Application.student_id == student.id,
        Application.status.in_(ACTIVE_STATUSES),
    ).first()
    if active:
        raise Conflict(f"you already have an active application (status: {active.status})")

    if room_preference not in VALID_ROOM_PREFS:
        raise Conflict("room_preference must be any, single or shared")

    app_row = Application(student_id=student.id, room_preference=room_preference, notes=notes)
    if preferred_hostel_id:
        hostel = db.session.get(Hostel, preferred_hostel_id)
        if not hostel:
            raise Conflict("preferred hostel not found")
        if hostel.gender != "mixed" and student.gender and hostel.gender != student.gender:
            raise Conflict(f"this hostel is restricted to {hostel.gender} students")
        app_row.preferred_hostel_id = hostel.id

    db.session.add(app_row)
    db.session.commit()
    return app_row


def get_application(app_id):
    app_row = db.session.get(Application, app_id)
    if not app_row:
        raise NotFound("application not found")
    return app_row


def list_applications(student_id=None, status=None):
    query = Application.query
    if student_id:
        query = query.filter(Application.student_id == student_id)
    if status:
        query = query.filter(Application.status == status)
    return query.order_by(Application.created_at.desc()).all()


def review_application(app_id, action, notes=None, reviewer_id=None):
    app_row = db.session.get(Application, app_id)
    if not app_row:
        raise NotFound("application not found")
    if app_row.status == "allocated":
        raise Conflict("application is already allocated")
    if action not in ("approve", "reject", "under_review"):
        raise Conflict("action must be approve, reject or under_review")

    status_map = {"approve": "approved", "reject": "rejected", "under_review": "under_review"}
    new_status = status_map[action]
    if app_row.status == new_status:
        raise Conflict(f"application is already {new_status}")

    app_row.status = new_status
    if notes is not None:
        app_row.review_notes = notes
    app_row.reviewed_by = reviewer_id
    app_row.reviewed_at = datetime.utcnow()

    msgs = {
        "approved": "Your hostel application has been approved. A room allocation will follow.",
        "rejected": "Your hostel application was rejected.",
        "under_review": "Your hostel application is now under review.",
    }
    message = msgs[new_status]
    if action == "reject" and notes:
        message = f"{message} {notes}"
    notify(app_row.student.user_id, "application", f"Application {new_status.replace('_', ' ')}", message)
    db.session.commit()
    return app_row
