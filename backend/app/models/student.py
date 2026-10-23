from datetime import datetime
from app.extensions import db


class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    registration_no = db.Column(db.String(40), index=True)
    program = db.Column(db.String(120))
    year_of_study = db.Column(db.Integer)
    phone = db.Column(db.String(30))
    gender = db.Column(db.String(10))
    verification_status = db.Column(db.String(20), nullable=False, default="unverified")
    verified_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="student")
    applications = db.relationship("Application", back_populates="student", lazy="dynamic")
    allocations = db.relationship("Allocation", back_populates="student", lazy="dynamic")
    payments = db.relationship("Payment", back_populates="student", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.user.full_name,
            "email": self.user.email,
            "registration_no": self.registration_no,
            "program": self.program,
            "year_of_study": self.year_of_study,
            "phone": self.phone,
            "gender": self.gender,
            "verification_status": self.verification_status,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
