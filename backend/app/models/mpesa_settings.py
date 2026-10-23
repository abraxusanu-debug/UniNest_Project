from datetime import datetime

from app.extensions import db


class MpesaSettings(db.Model):
    __tablename__ = "mpesa_settings"

    id = db.Column(db.Integer, primary_key=True)
    mpesa_enabled = db.Column(db.Boolean, default=False, nullable=False)
    mpesa_consumer_key = db.Column(db.String(255), nullable=True)
    mpesa_consumer_secret = db.Column(db.String(255), nullable=True)
    mpesa_shortcode = db.Column(db.String(50), nullable=True)
    mpesa_passkey = db.Column(db.String(255), nullable=True)
    mpesa_callback_url = db.Column(db.String(255), nullable=True)
    mpesa_environment = db.Column(db.String(20), default="sandbox", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @classmethod
    def get_or_create(cls):
        settings = cls.query.first()
        if settings is None:
            settings = cls()
            db.session.add(settings)
            db.session.commit()
        return settings
