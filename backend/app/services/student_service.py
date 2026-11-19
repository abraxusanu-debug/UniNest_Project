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
    if not password or len(str(password)) < 8:
        raise ServiceError("password must be at least 8 characters")

    registration_no = str(extras.get("registration_no") or "").strip()
    if registration_no and Student.query.filter_by(registration_no=registration_no).first():
        raise Conflict("registration number is already used by another student")

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

    try:
        from app.services.email_service import send_account_created_email

        send_account_created_email(user)
    except Exception:
        pass

    if settings.require_email_verification:
        try:
            from app.services.email_service import send_verification_email
            send_verification_email(user)
        except Exception:
            pass

    return user


def authenticate(email, password):
    from app.services.login_throttle import clear, is_locked, record_failure

    normalized_email = str(email).strip().lower()
    if is_locked(normalized_email):
        return None

    user = User.query.filter_by(email=normalized_email).first()
    if not user or not user.is_active or not user.check_password(str(password)):
        record_failure(normalized_email)
        return None

    settings = SiteSettings.get_or_create()
    if settings.require_email_verification and not user.email_verified:
        record_failure(normalized_email)
        return None

    clear(normalized_email)
    try:
        from app.services.email_service import send_login_alert_email

        send_login_alert_email(user)
    except Exception:
        pass
    return user


def create_maintenance_account(email, password, full_name):
    email = str(email).strip().lower()
    full_name = (full_name or "").strip()

    if "@" not in email:
        raise ServiceError("invalid email address")
    if not full_name:
        raise ServiceError("full name is required")
    if not password or len(str(password)) < 8:
        raise ServiceError("password must be at least 8 characters")
    if User.query.filter_by(email=email).first():
        raise Conflict("an account with this email already exists")

    user = User(email=email, full_name=full_name, role="maintenance", email_verified=True)
    user.set_password(str(password))
    db.session.add(user)
    db.session.commit()

    try:
        from app.services.email_service import send_account_created_email

        send_account_created_email(user)
    except Exception:
        pass
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

    if "registration_no" in data:
        new_registration_no = str(data["registration_no"]).strip() or None
        if new_registration_no:
            duplicate = Student.query.filter(
                Student.registration_no == new_registration_no,
                Student.id != student.id,
            ).first()
            if duplicate:
                raise Conflict("registration number is already used by another student")
        if student.registration_no != new_registration_no:
            student.registration_no = new_registration_no
            if student.verification_status == "verified":
                student.verification_status = "unverified"
                student.verified_at = None

    for field in ("program", "year_of_study", "phone", "gender"):
        if field in data:
            setattr(student, field, data[field])
    db.session.commit()
    return student
