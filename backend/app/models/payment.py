from datetime import datetime
from app.extensions import db
from sqlalchemy.orm import validates

PAYMENT_STATUSES = ("pending", "confirmed", "failed")
PAYMENT_METHODS = ("mpesa",)


class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(40), unique=True, nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False, index=True)
    allocation_id = db.Column(db.Integer, db.ForeignKey("allocations.id"))
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(5), default="KSh")
    method = db.Column(db.String(20), nullable=False, default="mpesa")
    phone_number = db.Column(db.String(30))
    semester = db.Column(db.String(30), default="2026 Semester 1")
    status = db.Column(db.String(20), nullable=False, default="pending", index=True)
    description = db.Column(db.String(255))
    confirmed_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    confirmed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship("Student", back_populates="payments")
    allocation = db.relationship("Allocation", back_populates="payments")
    confirmer = db.relationship("User", foreign_keys=[confirmed_by])

    @validates("status")
    def validate_status(self, key, value):
        if value not in PAYMENT_STATUSES:
            raise ValueError(f"invalid payment status: {value}")
        return value

    @validates("method")
    def validate_method(self, key, value):
        if value not in PAYMENT_METHODS:
            raise ValueError(f"invalid payment method: {value}")
        return value

    def to_dict(self):
        return {
            "id": self.id,
            "reference": self.reference,
            "student": {
                "id": self.student.id,
                "name": self.student.user.full_name,
                "registration_no": self.student.registration_no,
            },
            "allocation_id": self.allocation_id,
            "amount": self.amount,
            "currency": self.currency,
            "method": self.method,
            "phone_number": self.phone_number,
            "semester": self.semester,
            "status": self.status,
            "description": self.description,
            "confirmed_at": self.confirmed_at.isoformat() if self.confirmed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
