from flask import Blueprint, jsonify, request

from app.services import allocation_service
from app.services.errors import ServiceError
from app.utils import get_current_user, is_staff, role_required

bp = Blueprint("allocations", __name__, url_prefix="/api/allocations")


def _error(e):
    return jsonify({"error": e.kind, "message": e.message}), e.status


@bp.post("")
@role_required("admin")
def create_allocation():
    data = request.get_json(silent=True) or {}
    if not data.get("application_id") or not data.get("bed_id"):
        return jsonify({"error": "bad_request", "message": "application_id and bed_id are required"}), 400
    try:
        allocation = allocation_service.create_allocation(
            data["application_id"], data["bed_id"], get_current_user().id
        )
    except ServiceError as e:
        return _error(e)
    return jsonify(allocation.to_dict()), 201


@bp.get("")
def list_allocations():
    status = request.args.get("status")
    if not is_staff():
        me = get_current_user()
        if me.role != "student":
            return jsonify({"error": "forbidden", "message": "insufficient permissions"}), 403
        items = allocation_service.list_allocations(me.student.id, status)
    else:
        items = allocation_service.list_allocations(None, status)
    return jsonify({"allocations": [a.to_dict() for a in items], "count": len(items)})


@bp.get("/<int:allocation_id>")
def get_allocation(allocation_id):
    try:
        allocation = allocation_service.get_allocation(allocation_id)
    except ServiceError as e:
        return _error(e)
    user = get_current_user()
    if user.role == "student" and allocation.student.user_id != user.id:
        return jsonify({"error": "forbidden", "message": "you cannot view another student's allocation"}), 403
    return jsonify(allocation.to_dict())


@bp.post("/<int:allocation_id>/check-in")
@role_required("admin", "management")
def check_in(allocation_id):
    try:
        allocation = allocation_service.check_in(allocation_id)
    except ServiceError as e:
        return _error(e)
    return jsonify(allocation.to_dict())


@bp.post("/<int:allocation_id>/check-out")
@role_required("admin", "management")
def check_out(allocation_id):
    try:
        allocation = allocation_service.check_out(allocation_id)
    except ServiceError as e:
        return _error(e)
    return jsonify(allocation.to_dict())


@bp.delete("/<int:allocation_id>")
@role_required("admin")
def cancel_allocation(allocation_id):
    try:
        allocation = allocation_service.cancel(allocation_id)
    except ServiceError as e:
        return _error(e)
    return jsonify(allocation.to_dict())
