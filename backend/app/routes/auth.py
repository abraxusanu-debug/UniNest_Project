from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token
from flask import current_app

from app.extensions import db
from app.models import Student, User
from app.services import student_service
from app.services.errors import ServiceError
from app.utils import get_current_user

bp = Blueprint("auth", __name__, url_prefix="/api/auth")

VALID_STUDENT_FIELDS = ("registration_no", "program", "year_of_study", "phone", "gender")


@bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    required = ("email", "password", "full_name")
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": "bad_request", "message": f"missing fields: {', '.join(missing)}"}), 400

    try:
        user = student_service.register_student(
            data["email"], data["password"], data["full_name"], {f: data[f] for f in VALID_STUDENT_FIELDS if data.get(f)}
        )
    except ServiceError as e:
        return jsonify({"error": e.kind, "message": e.message}), e.status

    token = create_access_token(identity=str(user.id), additional_claims={"role": user.role, "email": user.email})
    return jsonify({"token": token, "user": user.to_dict()}), 201


@bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    if not data.get("email") or not data.get("password"):
        return jsonify({"error": "bad_request", "message": "email and password required"}), 400

    try:
        user = student_service.authenticate(data["email"], data["password"])
    except Exception:
        current_app.logger.exception("Login authentication failed")
        return jsonify({"error": "authentication_unavailable", "message": "authentication service could not access the database"}), 503

    if user:
        token = create_access_token(identity=str(user.id), additional_claims={"role": user.role, "email": user.email})
        return jsonify({"token": token, "user": user.to_dict()})
    return jsonify({"error": "unauthorized", "message": "invalid email or password"}), 401


@bp.get("/me")
def me():
    user = get_current_user()
    if not user:
        return jsonify({"error": "unauthorized", "message": "user no longer exists"}), 401
    return jsonify(user.to_dict())
