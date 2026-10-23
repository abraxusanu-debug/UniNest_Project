from datetime import datetime

from app.extensions import db


class SiteSettings(db.Model):
    __tablename__ = "site_settings"

    id = db.Column(db.Integer, primary_key=True)
    site_email = db.Column(db.String(120), default="hello@uninest.ac.ke")
    site_email_password = db.Column(db.String(255), nullable=True)
    smtp_server = db.Column(db.String(120), default="smtp.gmail.com")
    smtp_port = db.Column(db.Integer, default=587)
    use_tls = db.Column(db.Boolean, default=True)
    sender_name = db.Column(db.String(80), default="UniNest")
    require_email_verification = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @classmethod
    def get_or_create(cls):
        settings = cls.query.first()
        if settings:
            return settings
        settings = cls()
        db.session.add(settings)
        db.session.commit()
        return settings
