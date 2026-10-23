from datetime import datetime
from app.extensions import db
from sqlalchemy.orm import validates

REQ_STATUSES = ("submitted", "in_progress", "resolved")
PRIORITIES = ("low", "medium", "high")


class MaintenanceRequest(db.Model):
    __tablename__ = "maintenance_requests"

    id = db.Column(db.Integer, primary_key=True)
    allocation_id = db.Column(db.Integer, db.ForeignKey("allocations.id"))
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False, index=True)
    title = db.Column(db.String(140), nullable=False)
    description = db.Column(db.String(500))
    priority = db.Column(db.String(10), nullable=False, default="low")
    status = db.Column(db.String(20), nullable=False, default="submitted", index=True)
    resolution_note = db.Column(db.String(500))
    resolved_at = db.Column(db.DateTime)
    resolved_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    allocation = db.relationship("Allocation")
    student = db.relationship("Student")
    resolver = db.relationship("User", foreign_keys=[resolved_by])

    @validates("priority")
    def validate_priority(self, key, value):
        if value not in PRIORITIES:
            raise ValueError(f"invalid priority: {value}")
        return value

    @validates("status")
    def validate_status(self, key, value):
        if value not in REQ_STATUSES:
            raise ValueError(f"invalid maintenance status: {value}")
        return value

    def to_dict(self):
        alloc = self.allocation
        room_info = None
        if alloc:
            room_info = {
                "allocation_id": alloc.id,
                "hostel": alloc.bed.room.hostel.name,
                "room": alloc.bed.room.number,
            }
        return {
            "id": self.id,
            "student": {
                "id": self.student.id,
                "name": self.student.user.full_name,
                "email": self.student.user.email,
            },
            "room": room_info,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "status": self.status,
            "resolution_note": self.resolution_note,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
