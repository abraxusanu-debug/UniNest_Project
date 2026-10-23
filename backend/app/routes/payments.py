from flask import Blueprint, jsonify, request

from app.services import payment_service
from app.services.errors import ServiceError
from app.utils import get_current_user, role_required

bp = Blueprint("payments", __name__, url_prefix="/api/payments")


def _error(e):
    return jsonify({"error": e.kind, "message": e.message}), e.status


@bp.post("")
@role_required("student", "admin")
def create_payment():
    user = get_current_user()
    data = request.get_json(silent=True) or {}

    try:
        if user.role == "student":
            payment = payment_service.record_payment(
                user.student.id,
                data.get("amount"),
                data.get("method", "mpesa"),
                data.get("allocation_id"),
                data.get("semester"),
                data.get("description"),
            )
        else:
            from app.extensions import db
            from app.models import Allocation

            allocation_id = data.get("allocation_id")
            student_id = data.get("student_id")
            if allocation_id:
                allocation = db.session.get(Allocation, allocation_id)
                if not allocation:
                    return jsonify({"error": "not_found", "message": "allocation not found"}), 404
                student_id = allocation.student_id
            elif not student_id:
                return jsonify({"error": "bad_request", "message": "student_id or allocation_id is required for admin payments"}), 400
            payment = payment_service.record_payment(
                int(student_id), data.get("amount"), data.get("method", "mpesa"), allocation_id, data.get("semester"), data.get("description")
            )
    except ServiceError as e:
        return _error(e)

    return jsonify(payment.to_dict()), 201


@bp.get("")
def list_payments():
    user = get_current_user()
    if user.role == "student":
        items = payment_service.list_payments(user.student.id, request.args.get("status"))
    else:
        items = payment_service.list_payments(None, request.args.get("status"))
    return jsonify({"payments": [p.to_dict() for p in items], "count": len(items)})


@bp.get("/<int:payment_id>")
def get_payment(payment_id):
    try:
        payment = payment_service.get_payment(payment_id)
    except ServiceError as e:
        return _error(e)
    user = get_current_user()
    if user.role == "student" and payment.student.user_id != user.id:
        return jsonify({"error": "forbidden", "message": "you cannot view another student's payment"}), 403
    return jsonify(payment.to_dict())


@bp.post("/<int:payment_id>/confirm")
@role_required("admin")
def confirm_payment(payment_id):
    try:
        payment = payment_service.confirm(payment_id, get_current_user().id)
    except ServiceError as e:
        return _error(e)
    return jsonify(payment.to_dict())


@bp.post("/<int:payment_id>/fail")
@role_required("admin")
def fail_payment(payment_id):
    try:
        payment = payment_service.fail(payment_id, get_current_user().id)
    except ServiceError as e:
        return _error(e)
    return jsonify(payment.to_dict())
