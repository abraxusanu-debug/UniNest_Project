from flask import Blueprint, jsonify, request

from app.services import maintenance_service
from app.services.errors import ServiceError
from app.utils import get_current_user, role_required

bp = Blueprint("maintenance", __name__, url_prefix="/api/maintenance")


def _error(e):
    return jsonify({"error": e.kind, "message": e.message}), e.status


@bp.post("")
@role_required("student", "admin")
def create_request():
    user = get_current_user()
    data = request.get_json(silent=True) or {}

    try:
        if user.role == "student":
            req = maintenance_service.create_request(
                user.student.id, data.get("title"), data.get("description"), data.get("priority", "low"), data.get("allocation_id")
            )
        else:
            from app.extensions import db
            from app.models import Allocation

            allocation_id = data.get("allocation_id")
            if allocation_id:
                allocation = db.session.get(Allocation, allocation_id)
                if not allocation:
                    return jsonify({"error": "not_found", "message": "allocation not found"}), 404
                student_id = allocation.student_id
            elif data.get("student_id"):
                student_id = int(data["student_id"])
            else:
                return jsonify({"error": "bad_request", "message": "admin-submitted requests need student_id or a valid allocation_id"}), 400
            req = maintenance_service.create_request(
                student_id, data.get("title"), data.get("description"), data.get("priority", "low"), allocation_id
            )
    except ServiceError as e:
        return _error(e)
    return jsonify(req.to_dict()), 201


@bp.get("")
def list_requests():
    user = get_current_user()
    if user.role == "student":
        items = maintenance_service.list_requests(user.student.id, request.args.get("status"))
    else:
        items = maintenance_service.list_requests(None, request.args.get("status"))
    return jsonify({"requests": [r.to_dict() for r in items], "count": len(items)})


@bp.post("/<int:req_id>/status")
@role_required("admin")
def update_status(req_id):
    data = request.get_json(silent=True) or {}
    try:
        req = maintenance_service.update_status(req_id, data.get("status"), data.get("resolution_note"), get_current_user().id)
    except ServiceError as e:
        return _error(e)
    return jsonify(req.to_dict())
