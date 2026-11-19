from datetime import datetime, date

from app.extensions import db
from app.models import Allocation, Application, Bed
from app.services.errors import Conflict, NotFound
from app.services.common import notify


def create_allocation(application_id, bed_id, admin_id):
    app_row = db.session.get(Application, application_id)
    if not app_row:
        raise NotFound("application not found")
    if app_row.status != "approved":
        raise Conflict(f"application status must be approved (currently: {app_row.status})")
    if app_row.allocations.filter_by(status="allocated").first() or app_row.allocations.filter_by(status="checked_in").first():
        raise Conflict("application already has an active allocation")

    bed = db.session.get(Bed, bed_id)
    if not bed:
        raise NotFound("bed not found")
    if bed.status != "available":
        raise Conflict(f"bed is not available (currently: {bed.status})")

    existing = Allocation.query.filter(
        Allocation.student_id == app_row.student_id,
        Allocation.status.in_(("allocated", "checked_in")),
    ).first()
    if existing:
        raise Conflict("student already holds an active allocation")

    allocation = Allocation(
        student_id=app_row.student_id,
        bed_id=bed.id,
        application_id=app_row.id,
        allocated_by=admin_id,
    )
    bed.status = "occupied"
    app_row.status = "allocated"
    db.session.add(allocation)
    notify(
        app_row.student.user_id,
        "allocation",
        "Room allocated",
        f"You have been allocated bed {bed.bed_number} in room {bed.room.number}, {bed.room.hostel.name}. Complete your payment to confirm accommodation.",
    )
    db.session.commit()
    return allocation


def get_allocation(allocation_id):
    allocation = db.session.get(Allocation, allocation_id)
    if not allocation:
        raise NotFound("allocation not found")
    return allocation


def list_allocations(student_id=None, status=None):
    query = Allocation.query
    if student_id:
        query = query.filter(Allocation.student_id == student_id)
    if status:
        query = query.filter(Allocation.status == status)
    return query.order_by(Allocation.allocated_at.desc()).all()


def check_in(allocation_id):
    allocation = db.session.get(Allocation, allocation_id)
    if not allocation:
        raise NotFound("allocation not found")
    if allocation.status != "allocated":
        raise Conflict(f"allocation must be in allocated state (currently: {allocation.status})")
    allocation.status = "checked_in"
    allocation.check_in_date = date.today()
    notify(allocation.student.user_id, "check_in", "Checked in", "Check-in recorded. Welcome to your hostel!")
    db.session.commit()
    return allocation


def check_out(allocation_id):
    allocation = db.session.get(Allocation, allocation_id)
    if not allocation:
        raise NotFound("allocation not found")
    if allocation.status != "checked_in":
        raise Conflict(f"student must be checked in first (currently: {allocation.status})")
    allocation.status = "checked_out"
    allocation.check_out_date = date.today()
    allocation.bed.status = "available"
    if allocation.application:
        allocation.application.status = "completed"
    notify(allocation.student.user_id, "check_out", "Checked out", "Your check-out has been recorded and your bed is now free.")
    db.session.commit()
    return allocation


def cancel(allocation_id, admin_id=None):
    allocation = db.session.get(Allocation, allocation_id)
    if not allocation:
        raise NotFound("allocation not found")
    if allocation.status == "checked_out":
        raise Conflict("allocation already closed")
    if allocation.application:
        allocation.application.status = "approved"
    allocation.bed.status = "available"
    allocation.status = "cancelled"
    notify(allocation.student.user_id, "allocation", "Allocation cancelled", "Your hostel allocation has been cancelled by administration.")
    db.session.commit()
    return allocation
