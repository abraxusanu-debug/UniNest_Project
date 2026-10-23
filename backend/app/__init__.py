import os

from flask import Flask, flash, jsonify, redirect, render_template, request, url_for

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

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    from flask_cors import CORS

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    from app import models  # noqa: F401  (ensure models register with SQLAlchemy)

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
    def internal(_e):
        return jsonify({"error": "internal_error", "message": "something went wrong"}), 500

    with app.app_context():
        db.create_all()
        _ensure_schema_compatibility()

    return app


def _ensure_schema_compatibility():
    from sqlalchemy import inspect

    inspector = inspect(db.engine)
    existing = {}
    for table_name in ("users", "hostels", "payments", "site_settings"):
        try:
            existing[table_name] = {c["name"] for c in inspector.get_columns(table_name)}
        except Exception:
            existing[table_name] = set()

    if "profile_image" not in existing["users"]:
        db.session.execute(db.text("ALTER TABLE users ADD COLUMN profile_image VARCHAR(500)"))
    if "email_verified" not in existing["users"]:
        db.session.execute(db.text("ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT 1"))
    if "verification_token" not in existing["users"]:
        db.session.execute(db.text("ALTER TABLE users ADD COLUMN verification_token VARCHAR(255)"))
    if "reset_token" not in existing["users"]:
        db.session.execute(db.text("ALTER TABLE users ADD COLUMN reset_token VARCHAR(255)"))

    if "image_url" not in existing["hostels"]:
        db.session.execute(db.text("ALTER TABLE hostels ADD COLUMN image_url VARCHAR(500)"))
    if "amenities" not in existing["hostels"]:
        db.session.execute(db.text("ALTER TABLE hostels ADD COLUMN amenities TEXT DEFAULT ''"))
    if "phone_number" not in existing["payments"]:
        db.session.execute(db.text("ALTER TABLE payments ADD COLUMN phone_number VARCHAR(30)"))

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

    db.session.commit()
