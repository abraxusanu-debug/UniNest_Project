from datetime import datetime
from typing import Optional

from app.extensions import db
from app.models import MaintenanceRequest, Allocation, Student
from app.services.errors import Conflict, NotFound
from app.services.common import notify


def create_request(student_id, title, description=None, priority="low", allocation_id=None):
    if not title:
        raise Conflict("title is required")
    if priority not in ("low", "medium", "high"):
        raise Conflict("priority must be low, medium or high")

    if allocation_id:
        allocation = db.session.get(Allocation, allocation_id)
        if not allocation or allocation.student_id != student_id:
            raise Conflict("invalid allocation for this student")
        allocation_id = allocation.id
    else:
        latest = (
            Allocation.query.filter(Allocation.student_id == student_id)
            .order_by(Allocation.allocated_at.desc())
            .first()
        )
        allocation_id = latest.id if latest else None

    req = MaintenanceRequest(
        allocation_id=allocation_id,
        student_id=student_id,
        title=title,
        description=description,
        priority=priority,
    )
    db.session.add(req)
    db.session.commit()
    return req


def get_request(req_id):
    req = db.session.get(MaintenanceRequest, req_id)
    if not req:
        raise NotFound("maintenance request not found")
    return req


def list_requests(student_id=None, status=None):
    query = MaintenanceRequest.query
    if student_id:
        query = query.filter(MaintenanceRequest.student_id == student_id)
    if status:
        query = query.filter(MaintenanceRequest.status == status)
    return query.order_by(MaintenanceRequest.created_at.desc()).all()


def update_status(req_id, status, resolution_note=None, admin_id=None):
    req = db.session.get(MaintenanceRequest, req_id)
    if not req:
        raise NotFound("maintenance request not found")
    if status not in ("submitted", "in_progress", "resolved"):
        raise Conflict("status must be submitted, in_progress or resolved")
    if req.status == "resolved" and status != "resolved":
        raise Conflict("resolved requests cannot be reopened")
    if req.status == status:
        raise Conflict(f"request is already {status}")

    req.status = status
    if status == "resolved":
        req.resolved_at = datetime.utcnow()
        req.resolved_by = admin_id
        if resolution_note is not None:
            req.resolution_note = resolution_note

    titles = {"in_progress": "Maintenance in progress", "resolved": "Maintenance resolved", "submitted": "Maintenance request received"}
    message = f"'{req.title}' is now {status.replace('_', ' ')}."
    if status == "resolved" and req.resolution_note:
        message = f"{message} {req.resolution_note}"
    notify(req.student.user_id, "maintenance", titles[status], message)
    db.session.commit()
    return req
