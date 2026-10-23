from flask import Flask


def register_blueprints(app: Flask):
    from app.routes.auth import bp as auth_bp
    from app.routes.students import bp as students_bp
    from app.routes.hostels import bp as hostels_bp
    from app.routes.applications import bp as applications_bp
    from app.routes.allocations import bp as allocations_bp
    from app.routes.payments import bp as payments_bp
    from app.routes.maintenance import bp as maintenance_bp
    from app.routes.notifications import bp as notifications_bp
    from app.routes.reports import bp as reports_bp

    for bp in (
        auth_bp,
        students_bp,
        hostels_bp,
        applications_bp,
        allocations_bp,
        payments_bp,
        maintenance_bp,
        notifications_bp,
        reports_bp,
    ):
        app.register_blueprint(bp)
