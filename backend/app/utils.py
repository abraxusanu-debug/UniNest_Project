from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt, get_jwt_identity, verify_jwt_in_request

from app.extensions import db
from app.models import User


def get_current_user():
    verify_jwt_in_request()
    user_id = get_jwt_identity()
    return db.session.get(User, int(user_id))


def is_admin():
    verify_jwt_in_request()
    return get_jwt().get("role") == "admin"


def is_staff():
    verify_jwt_in_request()
    return get_jwt().get("role") in ("admin", "management")


def role_required(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get("role") not in roles:
                return jsonify({"error": "forbidden", "message": "insufficient permissions"}), 403
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def json_body(*required_fields):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            from flask import request

            data = request.get_json(silent=True) or {}
            missing = [f for f in required_fields if not data.get(f)]
            if missing:
                return jsonify({"error": "bad_request", "message": f"missing fields: {', '.join(missing)}"}), 400
            return fn(*args, **kwargs)

        return wrapper

    return decorator
