from datetime import datetime
from app.extensions import db

ROLES = ("student", "admin", "management", "maintenance")


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    profile_image = db.Column(db.String(500), nullable=True)
    role = db.Column(db.String(20), nullable=False, default="student")
    is_active = db.Column(db.Boolean, default=True)
    email_verified = db.Column(db.Boolean, default=True)
    verification_token = db.Column(db.String(255), nullable=True, unique=True)
    reset_token = db.Column(db.String(255), nullable=True, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship("Student", back_populates="user", uselist=False, cascade="all, delete-orphan")

    def set_password(self, password):
        from werkzeug.security import generate_password_hash

        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        from werkzeug.security import check_password_hash

        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        data = {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "profile_image": self.profile_image,
            "role": self.role,
            "is_active": self.is_active,
            "email_verified": self.email_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if self.role == "student" and self.student:
            data["verification_status"] = self.student.verification_status
            data["registration_no"] = self.student.registration_no
        return data
