from flask import Blueprint, jsonify, request

from app.extensions import db
from app.services import student_service
from app.services.errors import ServiceError
from app.utils import get_current_user, role_required

bp = Blueprint("students", __name__, url_prefix="/api/students")


@bp.get("/me")
@role_required("student")
def my_profile():
    return jsonify(get_current_user().student.to_dict())


@bp.put("/me")
@role_required("student")
def update_my_profile():
    me = get_current_user().student
    student_service.update_profile(me, request.get_json(silent=True) or {})
    return jsonify(me.to_dict())


@bp.get("")
@role_required("admin")
def list_students():
    students = student_service.list_students(request.args.get("status"))
    return jsonify({"students": [s.to_dict() for s in students], "count": len(students)})


@bp.post("/<int:student_id>/verify")
@role_required("admin")
def verify_student(student_id):
    try:
        student = student_service.verify_student(student_id, (request.get_json(silent=True) or {}).get("action", "verify"))
    except ServiceError as e:
        return jsonify({"error": e.kind, "message": e.message}), e.status
    return jsonify(student.to_dict())
