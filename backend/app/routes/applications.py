from flask import Blueprint, jsonify, request

from app.services import application_service
from app.services.errors import ServiceError
from app.utils import get_current_user, is_admin, is_staff, role_required

bp = Blueprint("applications", __name__, url_prefix="/api/applications")


def _error(e):
    return jsonify({"error": e.kind, "message": e.message}), e.status


@bp.post("")
@role_required("student")
def create_application():
    me = get_current_user()
    data = request.get_json(silent=True) or {}
    try:
        app_row = application_service.create_application(
            me.student, data.get("room_preference", "any"), data.get("notes"), data.get("preferred_hostel_id")
        )
    except ServiceError as e:
        return _error(e)
    return jsonify(app_row.to_dict()), 201


@bp.get("")
def list_applications():
    status = request.args.get("status")
    if is_admin():
        apps = application_service.list_applications(None, status)
    else:
        me = get_current_user()
        if me.role == "student":
            apps = application_service.list_applications(me.student.id, status)
        elif is_staff():
            apps = application_service.list_applications(None, "approved" if not status else status)
        else:
            return jsonify({"error": "forbidden", "message": "insufficient permissions"}), 403
    return jsonify({"applications": [a.to_dict() for a in apps], "count": len(apps)})


@bp.get("/<int:app_id>")
def get_application(app_id):
    try:
        app_row = application_service.get_application(app_id)
    except ServiceError as e:
        return _error(e)
    user = get_current_user()
    if user.role == "student" and app_row.student.user_id != user.id:
        return jsonify({"error": "forbidden", "message": "you cannot view another student's application"}), 403
    return jsonify(app_row.to_dict())


@bp.post("/<int:app_id>/review")
@role_required("admin")
def review_application(app_id):
    data = request.get_json(silent=True) or {}
    try:
        app_row = application_service.review_application(
            app_id, data.get("action"), data.get("notes"), get_current_user().id
        )
    except ServiceError as e:
        return _error(e)
    return jsonify(app_row.to_dict())
