import os
import secrets
import uuid
from functools import wraps

import csv
import io

from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, session, url_for
from flask import Response
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import Hostel, MpesaSettings, Room, SiteSettings, Student, User
from app.services import (
    allocation_service,
    application_service,
    hostel_service,
    maintenance_service,
    payment_service,
    report_service,
    student_service,
)
from app.services.errors import ServiceError

bp = Blueprint("web", __name__)


@bp.app_context_processor
def template_context():
    user = current_user()
    unread = 0
    if user:
        unread = report_service.unread_counts(user.id)
    return {"current_user": user, "unread_count": unread}


def current_user():
    uid = session.get("uid")
    return db.session.get(User, uid) if uid else None


def login_required(roles=None):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = current_user()
            if not user:
                return redirect(url_for("web.login"))
            if roles and user.role not in roles:
                flash("You do not have access to that area.", "error")
                return redirect(url_for("web.dashboard"))
            return fn(*args, user=user, **kwargs)

        return wrapper

    return decorator


def _error_redirect(e):
    flash(str(e.message), "error")
    return redirect(request.referrer or url_for("web.dashboard"))


def _form(field, default=None):
    return request.form.get(field) or default


def _as_bool(value, default=False):
    if value is None:
        return default
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"", "0", "false", "no", "off"}:
            return False
        if normalized in {"1", "true", "yes", "on"}:
            return True
    return bool(value)


@bp.get("/")
def index():
    hostels = [h.to_dict() for h in hostel_service.list_hostels()]
    total_free = sum(h["beds_available"] for h in hostels)
    total_beds = sum(h["beds_total"] for h in hostels)
    return render_template("index.html", hostels=hostels, total_free=total_free, total_beds=total_beds)


@bp.get("/dashboard")
def dashboard():
    user = current_user()
    if not user:
        return redirect(url_for("web.login"))
    target = {"student": "web.my_dashboard", "admin": "web.admin_dashboard", "management": "web.management_dashboard"}
    return redirect(url_for(target[user.role]))


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = student_service.authenticate(_form("email"), _form("password"))
        if not user:
            settings = SiteSettings.get_or_create()
            if settings.require_email_verification:
                flash("Please verify your email before logging in.", "error")
            else:
                flash("Invalid email or password.", "error")
            return redirect(url_for("web.login"))
        session["uid"] = user.id
        session["role"] = user.role
        session["name"] = user.full_name
        flash(f"Welcome back, {user.full_name.split()[0]}!", "success")
        return redirect(url_for("web.dashboard"))
    return render_template("auth/login.html")


@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        try:
            user = student_service.register_student(
                _form("email"), _form("password"), _form("full_name"),
                {f: _form(f) for f in ("registration_no", "program", "year_of_study", "phone", "gender")},
            )
        except ServiceError as e:
            flash(str(e.message), "error")
            return redirect(url_for("web.register"))

        settings = SiteSettings.get_or_create()
        if settings.require_email_verification:
            session.clear()
            flash("Account created. Please check your email to verify your account before logging in.", "success")
            return redirect(url_for("web.login"))

        session["uid"] = user.id
        session["role"] = user.role
        session["name"] = user.full_name
        flash("Account created. You will be notified once the hostel office verifies your account.", "success")
        return redirect(url_for("web.my_dashboard"))
    return render_template("auth/register.html")


@bp.route("/verify-email/<token>")
def verify_email(token):
    user = User.query.filter_by(verification_token=token).first()
    if not user:
        flash("This verification link is invalid or expired.", "error")
        return redirect(url_for("web.login"))
    user.email_verified = True
    user.verification_token = None
    db.session.commit()
    flash("Email verified successfully. You can now log in.", "success")
    return redirect(url_for("web.login"))


@bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        user = User.query.filter_by(email=email).first()
        if user:
            user.reset_token = secrets.token_urlsafe(20)
            db.session.commit()
            try:
                from app.services.email_service import send_password_reset_email
                send_password_reset_email(user)
            except Exception:
                pass
        flash("If that email is registered, a reset link has been sent.", "info")
        return redirect(url_for("web.login"))
    return render_template("auth/forgot_password.html")


@bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first()
    if not user:
        flash("This reset link is invalid or expired.", "error")
        return redirect(url_for("web.login"))

    if request.method == "POST":
        password = (request.form.get("password") or "").strip()
        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "error")
            return redirect(request.url)
        user.set_password(password)
        user.reset_token = None
        db.session.commit()
        flash("Your password has been updated. Please log in again.", "success")
        return redirect(url_for("web.login"))

    return render_template("auth/reset_password.html")


@bp.get("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("web.login"))


@bp.get("/my/dashboard")
@login_required(["student"])
def my_dashboard(user):
    student = user.student
    apps = application_service.list_applications(student.id)
    app_row = apps[0] if apps else None
    allocation = allocation_service.list_allocations(student.id)
    active_alloc = next((a for a in allocation if a.status in ("allocated", "checked_in")), allocation[0] if allocation else None)
    payments = payment_service.list_payments(student.id)
    maintenance = maintenance_service.list_requests(student.id)
    unread = report_service.unread_counts(user.id)
    return render_template(
        "student/dashboard.html",
        app_row=app_row,
        allocation=active_alloc,
        allocation_other=[a for a in allocation if a is not active_alloc],
        payments=payments,
        maintenance=maintenance,
        unread=unread,
        student=student,
    )


@bp.route("/my/apply", methods=["GET", "POST"])
@login_required(["student"])
def my_apply(user):
    if request.method == "POST":
        try:
            application_service.create_application(
                user.student, _form("room_preference", "any"), _form("notes"), int(_form("preferred_hostel_id")) if _form("preferred_hostel_id") else None
            )
            flash("Application submitted. The hostel office will review it.", "success")
            return redirect(url_for("web.my_dashboard"))
        except ServiceError as e:
            return _error_redirect(e)
    apps = application_service.list_applications(user.student.id)
    if any(a.status in ("pending", "under_review", "approved", "allocated") for a in apps):
        flash("You already have an active application.", "error")
        return redirect(url_for("web.my_dashboard"))
    return render_template("student/apply.html", hostels=hostel_service.list_hostels())


@bp.get("/my/availability")
@login_required(["student", "admin", "management"])
def my_availability(user):
    return render_template("student/availability.html", hostels=hostel_service.availability_overview(), now_role=user.role)


@bp.route("/my/payments", methods=["GET", "POST"])
@login_required(["student"])
def my_payments(user):
    if request.method == "POST":
        try:
            payment = payment_service.record_payment(
                user.student.id,
                _form("amount"),
                "mpesa",
                int(_form("allocation_id")) if _form("allocation_id") else None,
                _form("semester"),
                "Hostel accommodation fee",
                _form("phone_number"),
            )
            settings = MpesaSettings.get_or_create()
            payment = payment_service.initiate_mpesa_payment(payment.id, _form("phone_number"), settings)
            if payment.status == "confirmed":
                flash(f"M-Pesa prompt sent to {_form('phone_number')}. The payment was settled automatically.", "success")
            else:
                flash("M-Pesa is not configured yet. Your payment request is saved for admin review.", "info")
        except ServiceError as e:
            return _error_redirect(e)
        return redirect(url_for("web.my_payments"))
    allocations = allocation_service.list_allocations(user.student.id)
    return render_template("student/payments.html", payments=payment_service.list_payments(user.student.id), allocations=allocations)


@bp.route("/my/maintenance", methods=["GET", "POST"])
@login_required(["student"])
def my_maintenance(user):
    if request.method == "POST":
        try:
            maintenance_service.create_request(
                user.student.id, _form("title"), _form("description"), _form("priority", "low"), int(_form("allocation_id")) if _form("allocation_id") else None
            )
            flash("Maintenance request submitted.", "success")
        except ServiceError as e:
            return _error_redirect(e)
        return redirect(url_for("web.my_maintenance"))
    allocs = allocation_service.list_allocations(user.student.id)
    mine = maintenance_service.list_requests(user.student.id)
    return render_template("student/maintenance.html", requests=mine, allocations=allocs)


@bp.post("/my/notifications/read-all")
@login_required()
def my_notifications_read_all(user):
    from app.models import Notification

    Notification.query.filter_by(user_id=user.id, is_read=False).update({"is_read": True})
    db.session.commit()
    flash("All notifications marked as read.", "info")
    return redirect(request.referrer or url_for("web.my_dashboard"))


@bp.get("/hostels/<int:hostel_id>")
def hostel_detail(hostel_id):
    hostel = db.session.get(Hostel, hostel_id)
    if not hostel:
        flash("Hostel not found.", "error")
        return redirect(url_for("web.index"))
    rooms = hostel.rooms.order_by(Room.number).all()
    return render_template("hostel_detail.html", hostel=hostel, rooms=rooms)


@bp.get("/my/notifications")
def my_notifications():
    user = current_user()
    if not user:
        return redirect(url_for("web.login"))
    from app.models import Notification

    items = Notification.query.filter_by(user_id=user.id).order_by(Notification.created_at.desc()).all()
    return render_template("student/notifications.html", notifications=items)


def _save_upload(file_storage, folder_name):
    if not file_storage or not getattr(file_storage, "filename", None):
        return None
    folder = os.path.join(current_app.static_folder, "uploads", folder_name)
    os.makedirs(folder, exist_ok=True)
    filename = secure_filename(file_storage.filename)
    file_path = os.path.join(folder, f"{uuid.uuid4().hex}_{filename}")
    file_storage.save(file_path)
    relative = os.path.relpath(file_path, current_app.static_folder)
    return "/static/" + relative.replace(os.sep, "/")


@bp.route("/my/profile", methods=["GET", "POST"])
@login_required(["student"])
def my_profile(user):
    if request.method == "POST":
        try:
            data = request.form.to_dict()
            data.pop("csrf_token", None)
            uploaded = request.files.get("profile_image")
            if uploaded and uploaded.filename:
                data["profile_image"] = _save_upload(uploaded, "profiles")
            if data.get("profile_image_url"):
                data["profile_image_url"] = data["profile_image_url"].strip()
            student_service.update_profile(user.student, data)
        except Exception:
            flash("Profile update failed. Please try again.", "error")
            return redirect(url_for("web.my_profile"))
        flash("Profile updated.", "success")
        return redirect(url_for("web.my_profile"))
    return render_template("student/profile.html", student=user.student)


@bp.get("/admin/dashboard")
@login_required(["admin"])
def admin_dashboard(user):
    s = report_service.summary()
    students = student_service.list_students()
    open_maintenance = maintenance_service.list_requests(None)
    return render_template(
        "admin/dashboard.html",
        summary=s,
        students_count=len(students),
        unverified=sum(1 for x in students if x.verification_status != "verified"),
        maintenance_open=sum(1 for r in open_maintenance if r.status != "resolved"),
    )


@bp.get("/management/dashboard")
@login_required(["management"])
def management_dashboard(user):
    s = report_service.summary()
    return render_template("management/dashboard.html", summary=s)


@bp.get("/admin/students")
@login_required(["admin"])
def admin_students(user):
    return render_template("admin/students.html", students=student_service.list_students(request.args.get("status")), filter_status=request.args.get("status"))


@bp.post("/admin/students/<int:student_id>/verify")
@login_required(["admin"])
def admin_verify_student(student_id, user):
    try:
        student_service.verify_student(student_id, _form("action", "verify"))
        flash("Student verification updated.", "success")
    except ServiceError as e:
        return _error_redirect(e)
    return redirect(url_for("web.admin_students"))


@bp.get("/admin/hostels")
@login_required(["admin"])
def admin_hostels(user):
    return render_template("admin/hostels.html", hostels=hostel_service.list_hostels(), overview=hostel_service.availability_overview())


@bp.post("/admin/hostels")
@login_required(["admin"])
def admin_create_hostel(user):
    try:
        image_url = _form("image_url")
        uploaded = request.files.get("image_file")
        if uploaded and uploaded.filename:
            image_url = _save_upload(uploaded, "hostels") or image_url
        hostel_service.create_hostel(
            _form("name"),
            _form("gender", "mixed"),
            _form("location"),
            _form("description"),
            image_url,
            _form("amenities"),
        )
        flash("Hostel created.", "success")
    except ServiceError as e:
        return _error_redirect(e)
    return redirect(url_for("web.admin_hostels"))


@bp.post("/admin/hostels/<int:hostel_id>/rooms")
@login_required(["admin"])
def admin_create_room(hostel_id, user):
    try:
        hostel_service.create_room(
            hostel_id, _form("number"), int(_form("floor")) if _form("floor") else None, _form("room_type", "shared"), int(_form("bed_count")) if _form("bed_count") else None
        )
        flash("Room added.", "success")
    except ServiceError as e:
        return _error_redirect(e)
    except ValueError:
        flash("Floor and bed count must be numbers.", "error")
    return redirect(url_for("web.admin_hostels"))


@bp.post("/admin/rooms/<int:room_id>/beds")
@login_required(["admin"])
def admin_add_beds(room_id, user):
    try:
        hostel_service.add_beds(room_id, int(_form("count", 1)))
        flash("Beds added.", "success")
    except ServiceError as e:
        return _error_redirect(e)
    except ValueError:
        flash("Bed count must be a number.", "error")
    return redirect(url_for("web.admin_hostels"))


@bp.post("/admin/beds/<int:bed_id>/status")
@login_required(["admin"])
def admin_bed_status(bed_id, user):
    try:
        hostel_service.update_bed(bed_id, {"status": _form("status")})
        flash("Bed status updated.", "success")
    except ServiceError as e:
        return _error_redirect(e)
    return redirect(url_for("web.admin_hostels"))


@bp.post("/admin/hostels/<int:hostel_id>/delete")
@login_required(["admin"])
def admin_delete_hostel(hostel_id, user):
    try:
        hostel_service.delete_hostel(hostel_id)
        flash("Hostel deleted.", "success")
    except ServiceError as e:
        return _error_redirect(e)
    return redirect(url_for("web.admin_hostels"))


@bp.post("/admin/rooms/<int:room_id>/delete")
@login_required(["admin"])
def admin_room_delete(room_id, user):
    try:
        hostel_service.delete_room(room_id)
        flash("Room deleted.", "success")
    except ServiceError as e:
        return _error_redirect(e)
    return redirect(url_for("web.admin_hostels"))


@bp.route("/admin/applications", methods=["GET", "POST"])
@login_required(["admin"])
def admin_applications(user):
    if request.method == "POST":
        try:
            if _form("review_action"):
                application_service.review_application(int(_form("application_id")), _form("review_action"), _form("review_notes"), user.id)
                flash("Application reviewed.", "success")
            elif _form("allocate_action"):
                allocation_service.create_allocation(int(_form("application_id")), int(_form("bed_id")), user.id)
                flash("Bed allocated.", "success")
        except ServiceError as e:
            return _error_redirect(e)
        except ValueError:
            flash("Invalid selection.", "error")
        return redirect(url_for("web.admin_applications"))
    status = request.args.get("status") or "pending"
    apps = application_service.list_applications(None, None if status == "all" else status)
    free = _free_bed_choices() if status == "approved" else []
    return render_template("admin/applications.html", applications=apps, status=status, free_beds=free)


def _free_bed_choices():
    choices = []
    for h in hostel_service.list_hostels():
        for r in h.rooms:
            for bed in r.beds.filter_by(status="available"):
                label = f"{h.name} / Room {r.number} / Bed {bed.bed_number}"
                choices.append({"id": bed.id, "label": label})
    return choices


@bp.get("/admin/allocations")
@login_required(["admin", "management"])
def admin_allocations(user):
    return render_template("admin/allocations.html", allocations=allocation_service.list_allocations())


@bp.post("/admin/allocations/<int:allocation_id>/<action>")
@login_required(["admin", "management"])
def admin_allocation_action(allocation_id, action, user):
    try:
        if action == "check-in":
            allocation_service.check_in(allocation_id)
        elif action == "check-out":
            allocation_service.check_out(allocation_id)
        elif action == "cancel":
            allocation_service.cancel(allocation_id)
        else:
            flash("Unknown action.", "error")
            return redirect(url_for("web.admin_allocations"))
        flash("Allocation updated.", "success")
    except ServiceError as e:
        return _error_redirect(e)
    return redirect(url_for("web.admin_allocations"))


@bp.route("/admin/payments", methods=["GET", "POST"])
@login_required(["admin"])
def admin_payments(user):
    if request.method == "POST":
        try:
            if _form("payment_action") == "confirm":
                payment_service.confirm(int(_form("payment_id")), user.id)
                flash("Payment confirmed.", "success")
            elif _form("payment_action") == "fail":
                payment_service.fail(int(_form("payment_id")), user.id)
                flash("Payment marked as not accepted.", "info")
        except ServiceError as e:
            return _error_redirect(e)
        return redirect(url_for("web.admin_payments"))

    settings = MpesaSettings.get_or_create()
    email_settings = SiteSettings.get_or_create()
    return render_template(
        "admin/payments.html",
        payments=payment_service.list_payments(None, request.args.get("status")),
        req_status=request.args.get("status"),
        mpesa_settings=settings,
        email_settings=email_settings,
    )


@bp.route("/admin/payments/settings", methods=["POST"])
@login_required(["admin"])
def admin_payment_settings(user):
    settings = MpesaSettings.get_or_create()
    settings.mpesa_enabled = _as_bool(_form("mpesa_enabled"))
    settings.mpesa_consumer_key = _form("mpesa_consumer_key", "").strip()
    settings.mpesa_consumer_secret = _form("mpesa_consumer_secret", "").strip()
    settings.mpesa_shortcode = _form("mpesa_shortcode", "").strip()
    settings.mpesa_passkey = _form("mpesa_passkey", "").strip()
    settings.mpesa_callback_url = _form("mpesa_callback_url", "").strip()
    settings.mpesa_environment = _form("mpesa_environment", "sandbox").strip() or "sandbox"
    db.session.add(settings)

    email_settings = SiteSettings.get_or_create()
    email_settings.site_email = _form("site_email", "").strip()
    email_settings.site_email_password = _form("site_email_password", "").strip()
    email_settings.smtp_server = _form("smtp_server", "smtp.gmail.com").strip() or "smtp.gmail.com"
    email_settings.smtp_port = int(_form("smtp_port", 587) or 587)
    email_settings.use_tls = _as_bool(_form("use_tls"))
    email_settings.sender_name = _form("sender_name", "UniNest").strip() or "UniNest"
    email_settings.require_email_verification = _as_bool(_form("require_email_verification"))
    db.session.add(email_settings)
    db.session.commit()
    flash("Daraja and email settings saved successfully.", "success")
    return redirect(url_for("web.admin_payments"))


@bp.route("/admin/maintenance", methods=["GET", "POST"])
@login_required(["admin"])
def admin_maintenance(user):
    if request.method == "POST":
        try:
            maintenance_service.update_status(int(_form("request_id")), _form("status"), _form("resolution_note"), user.id)
            flash("Maintenance request updated.", "success")
        except ServiceError as e:
            return _error_redirect(e)
        return redirect(url_for("web.admin_maintenance"))
    return render_template("admin/maintenance.html", requests=maintenance_service.list_requests(None, request.args.get("status")), req_status=request.args.get("status"))


@bp.get("/reports")
@login_required(["admin", "management"])
def reports(user):
    summary_data = report_service.summary()
    occupancy = report_service.occupancy_rows()
    vacancies, total_free = report_service.vacancy_rows()
    payments = report_service.payments_report()
    return render_template(
        "reports.html",
        s=summary_data,
        occupancy=occupancy,
        vacancies=vacancies,
        vacancies_total=total_free,
        paym=payments,
    )


@bp.get("/reports/occupancy.csv")
@login_required(["admin", "management"])
def reports_occupancy_csv(user):
    rows = report_service.occupancy_rows()
    mapped = [
        {"Hostel": r["hostel"], "Rooms": r["rooms"], "Beds Total": r["beds_total"], "Beds Occupied": r["beds_occupied"], "Beds Available": r["beds_available"], "Occupancy %": r["occupancy_rate"]}
        for r in rows
    ]
    import csv
    import io

    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=["Hostel", "Rooms", "Beds Total", "Beds Occupied", "Beds Available", "Occupancy %"])
    writer.writeheader()
    writer.writerows(mapped)
    return Response(out.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=occupancy.csv"})


@bp.get("/reports/allocations.csv")
@login_required(["admin", "management"])
def reports_allocations_csv(user):
    mapped = report_service.allocation_rows()
    mapped = [
        {"Student": r["student"], "Registration No": r["registration_no"], "Hostel": r["hostel"], "Room": r["room"], "Bed": r["bed"], "Status": r["status"], "Paid": r["paid"], "Allocated At": r["allocated_at"]}
        for r in mapped
    ]
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=["Student", "Registration No", "Hostel", "Room", "Bed", "Status", "Paid", "Allocated At"])
    writer.writeheader()
    writer.writerows(mapped)
    return Response(out.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=allocations.csv"})
