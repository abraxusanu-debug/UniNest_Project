import secrets
from datetime import datetime

from app.extensions import db
from app.models import User, Student, SiteSettings
from app.services.errors import Conflict, NotFound, ServiceError
from app.services.common import notify


def register_student(email, password, full_name, extras=None):
    extras = extras or {}
    email = str(email).strip().lower()

    if "@" not in email:
        raise ServiceError("invalid email address")
    if not password or len(str(password)) < 6:
        raise ServiceError("password must be at least 6 characters")
    if User.query.filter_by(email=email).first():
        raise Conflict("an account with this email already exists")

    settings = SiteSettings.get_or_create()
    email_verified = not settings.require_email_verification

    user = User(
        email=email,
        full_name=(full_name or "").strip(),
        role="student",
        profile_image=extras.get("profile_image") or extras.get("profile_image_url"),
        email_verified=email_verified,
        verification_token=secrets.token_urlsafe(16) if settings.require_email_verification else None,
    )
    user.set_password(str(password))

    student = Student()
    for field in ("registration_no", "program", "year_of_study", "phone", "gender"):
        if extras.get(field):
            setattr(student, field, extras[field])
    user.student = student
    db.session.add(user)
    db.session.commit()

    if settings.require_email_verification:
        try:
            from app.services.email_service import send_verification_email
            send_verification_email(user)
        except Exception:
            pass

    return user


def authenticate(email, password):
    user = User.query.filter_by(email=str(email).strip().lower()).first()
    if not user or not user.check_password(str(password)):
        return None
    settings = SiteSettings.get_or_create()
    if settings.require_email_verification and not user.email_verified:
        return None
    return user


def verify_student(student_id, action="verify"):
    student = db.session.get(Student, student_id)
    if not student:
        raise NotFound("student not found")

    if action == "unverify":
        student.verification_status = "unverified"
        student.verified_at = None
    else:
        student.verification_status = "verified"
        student.verified_at = datetime.utcnow()
        notify(
            student.user_id,
            "verification",
            "Account verified",
            "Your student account has been verified. You can now apply for hostel accommodation.",
        )
    db.session.commit()
    return student


def list_students(status=None):
    query = Student.query
    if status in ("verified", "unverified"):
        query = query.filter(Student.verification_status == status)
    return query.order_by(Student.created_at.desc()).all()


def update_profile(student, data):
    user = student.user
    if "full_name" in data and data.get("full_name", "").strip():
        user.full_name = data["full_name"].strip()
    if "profile_image" in data and data.get("profile_image"):
        user.profile_image = data["profile_image"]
    if "profile_image_url" in data and data.get("profile_image_url"):
        user.profile_image = data["profile_image_url"]
    for field in ("program", "year_of_study", "phone", "gender", "registration_no"):
        if field in data:
            setattr(student, field, data[field])
    db.session.commit()
    return student
