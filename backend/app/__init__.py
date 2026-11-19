import os
import secrets

from flask import Flask, abort, flash, jsonify, redirect, render_template, request, session, url_for

from config import Config
from app.extensions import db, migrate, jwt


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def create_app(config_object=Config):
    app = Flask(
        __name__,
        template_folder=os.path.join(PROJECT_ROOT, "templates"),
        static_folder=os.path.join(PROJECT_ROOT, "static"),
    )
    app.config.from_object(config_object)
    app.json.sort_keys = False

    @app.context_processor
    def csrf_context():
        if not session.get("csrf_token"):
            session["csrf_token"] = secrets.token_urlsafe(32)
        return {"csrf_token": session["csrf_token"]}

    @app.before_request
    def protect_web_forms():
        if app.testing:
            return None
        if request.method not in ("POST", "PUT", "PATCH", "DELETE"):
            return None
        if request.path.startswith("/api/"):
            return None
        if not request.form:
            return None
        supplied = request.form.get("csrf_token")
        if not supplied or not session.get("csrf_token") or not secrets.compare_digest(supplied, session["csrf_token"]):
            abort(403)
        return None

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    from app import models  # noqa: F401  (ensure models register with SQLAlchemy)

    with app.app_context():
        db.create_all()
        _ensure_schema_compatibility()
        _ensure_deployment_accounts()

    from flask_cors import CORS

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    from app.routes.auth import bp as auth_bp
    from app.routes.students import bp as students_bp
    from app.routes.hostels import bp as hostels_bp
    from app.routes.applications import bp as applications_bp
    from app.routes.allocations import bp as allocations_bp
    from app.routes.payments import bp as payments_bp
    from app.routes.maintenance import bp as maintenance_bp
    from app.routes.notifications import bp as notifications_bp
    from app.routes.reports import bp as reports_bp
    from app.routes.web import bp as web_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(students_bp)
    app.register_blueprint(hostels_bp)
    app.register_blueprint(applications_bp)
    app.register_blueprint(allocations_bp)
    app.register_blueprint(payments_bp)
    app.register_blueprint(maintenance_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(web_bp)

    from app.services.errors import ServiceError

    @app.errorhandler(ServiceError)
    def service_error_handler(e):
        if request.path.startswith("/api/"):
            return jsonify({"error": e.kind, "message": str(e)}), e.status
        flash(str(e.message), "error")
        return redirect(request.referrer or url_for("index_page"))

    @app.route("/api/health")
    def health():
        return jsonify({"status": "ok", "service": "uninest", "version": "1.0.0"})

    @app.route("/")
    def index_page():
        return redirect(url_for("web.index"))

    @app.errorhandler(404)
    def not_found(_e):
        if request.path.startswith("/api/"):
            return jsonify({"error": "not_found", "message": "endpoint does not exist"}), 404
        flash("Page not found.", "error")
        return render_template("404.html"), 404

    @app.errorhandler(405)
    def method_not_allowed(_e):
        return jsonify({"error": "method_not_allowed", "message": "check the HTTP method"}), 405

    @app.errorhandler(500)
    def internal(error):
        app.logger.exception("Unhandled internal server error", exc_info=error)
        if request.path.startswith("/api/"):
            return jsonify({"error": "internal_error", "message": "the server encountered an unexpected error"}), 500
        flash("The server encountered an unexpected error. Please try again.", "error")
        return render_template("404.html"), 500

    return app


def _ensure_schema_compatibility():
    from sqlalchemy import inspect

    inspector = inspect(db.engine)
    existing = {}
    table_names = ("users", "hostels", "payments", "site_settings", "mpesa_settings")
    for table_name in table_names:
        try:
            existing[table_name] = {c["name"] for c in inspector.get_columns(table_name)}
        except Exception:
            existing[table_name] = set()

    changed = False

    for table_name, column_name, column_type in (
        ("users", "profile_image", "VARCHAR(500)"),
        ("users", "email_verified", "BOOLEAN DEFAULT 1"),
        ("users", "verification_token", "VARCHAR(255)"),
        ("users", "reset_token", "VARCHAR(255)"),
        ("hostels", "image_url", "VARCHAR(500)"),
        ("hostels", "amenities", "TEXT DEFAULT ''"),
        ("payments", "phone_number", "VARCHAR(30)"),
    ):
        if table_name not in inspector.get_table_names():
            continue
        if column_name not in existing[table_name]:
            db.session.execute(db.text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"))
            changed = True

    if "site_settings" in existing and existing["site_settings"]:
        required_site_columns = {
            "site_email": "VARCHAR(120)",
            "site_email_password": "VARCHAR(255)",
            "smtp_server": "VARCHAR(120)",
            "smtp_port": "INTEGER",
            "use_tls": "BOOLEAN",
            "sender_name": "VARCHAR(80)",
            "require_email_verification": "BOOLEAN",
        }
        for col_name, col_type in required_site_columns.items():
            if col_name not in existing["site_settings"]:
                db.session.execute(db.text(f"ALTER TABLE site_settings ADD COLUMN {col_name} {col_type}"))

    if "mpesa_settings" in existing and existing["mpesa_settings"]:
        if "accommodation_required_amount" not in existing["mpesa_settings"]:
            db.session.execute(db.text("ALTER TABLE mpesa_settings ADD COLUMN accommodation_required_amount NUMERIC(12, 2)"))

    db.session.commit()


def _ensure_deployment_accounts():
    if os.environ.get("UNINEST_BOOTSTRAP_ADMIN", "false").strip().lower() not in ("1", "true", "yes", "on"):
        return

    from app.models import User

    email = (os.environ.get("UNINEST_ADMIN_EMAIL") or "admin@uninest.ac.ke").strip().lower()
    password = os.environ.get("UNINEST_ADMIN_PASSWORD") or "Admin@123"
    user = User.query.filter_by(email=email).first()
    if user:
        return

    user = User(email=email, full_name="UniNest Administrator", role="admin", email_verified=True, is_active=True)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
