from datetime import datetime, date
from app.extensions import db

ALLOCATION_STATUSES = ("allocated", "checked_in", "checked_out", "cancelled")


class Allocation(db.Model):
    __tablename__ = "allocations"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False, index=True)
    bed_id = db.Column(db.Integer, db.ForeignKey("beds.id"), nullable=False)
    application_id = db.Column(db.Integer, db.ForeignKey("applications.id"))
    status = db.Column(db.String(20), nullable=False, default="allocated", index=True)
    paid = db.Column(db.Boolean, default=False)
    accommodation_confirmed = db.Column(db.Boolean, default=False)
    allocated_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    allocated_at = db.Column(db.DateTime, default=datetime.utcnow)
    check_in_date = db.Column(db.Date)
    check_out_date = db.Column(db.Date)

    student = db.relationship("Student", back_populates="allocations")
    bed = db.relationship("Bed")
    application = db.relationship("Application", back_populates="allocations")
    allocator = db.relationship("User", foreign_keys=[allocated_by])
    payments = db.relationship("Payment", back_populates="allocation", lazy="dynamic")

    def to_dict(self):
        room = self.bed.room
        hostel = room.hostel
        return {
            "id": self.id,
            "student": {
                "id": self.student.id,
                "name": self.student.user.full_name,
                "registration_no": self.student.registration_no,
                "email": self.student.user.email,
            },
            "bed": {
                "id": self.bed.id,
                "hostel": hostel.name,
                "room": room.number,
                "bed_number": self.bed.bed_number,
            },
            "status": self.status,
            "paid": self.paid,
            "accommodation_confirmed": self.accommodation_confirmed,
            "allocated_at": self.allocated_at.isoformat() if self.allocated_at else None,
            "check_in_date": self.check_in_date.isoformat() if self.check_in_date else None,
            "check_out_date": self.check_out_date.isoformat() if self.check_out_date else None,
        }
