from datetime import datetime
from app.extensions import db
from sqlalchemy.orm import validates
from app.models.allocation import Allocation

APP_STATUSES = ("pending", "under_review", "approved", "rejected", "allocated", "withdrawn", "completed")


class Application(db.Model):
    __tablename__ = "applications"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False, index=True)
    preferred_hostel_id = db.Column(db.Integer, db.ForeignKey("hostels.id"))
    room_preference = db.Column(db.String(20), default="any")
    notes = db.Column(db.String(255))
    status = db.Column(db.String(20), nullable=False, default="pending", index=True)
    review_notes = db.Column(db.String(255))
    reviewed_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    reviewed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    student = db.relationship("Student", back_populates="applications")
    preferred_hostel = db.relationship("Hostel")
    reviewer = db.relationship("User", foreign_keys=[reviewed_by])
    allocations = db.relationship("Allocation", back_populates="application", lazy="dynamic")

    @validates("status")
    def validate_status(self, key, value):
        if value not in APP_STATUSES:
            raise ValueError(f"invalid application status: {value}")
        return value

    def to_dict(self):
        allocation = self.allocations.order_by(Allocation.id.desc()).first()
        return {
            "id": self.id,
            "student": {
                "id": self.student.id,
                "name": self.student.user.full_name,
                "registration_no": self.student.registration_no,
                "email": self.student.user.email,
            },
            "preferred_hostel": self.preferred_hostel.name if self.preferred_hostel else None,
            "preferred_hostel_id": self.preferred_hostel_id,
            "room_preference": self.room_preference,
            "notes": self.notes,
            "status": self.status,
            "review_notes": self.review_notes,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "allocation_id": allocation.id if allocation else None,
        }
