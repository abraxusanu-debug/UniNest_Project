from app.models import Allocation, Application, Bed, Hostel, Payment, Notification


def summary():
    hostels = Hostel.query.all()
    beds_total = sum(h.beds_total for h in hostels)
    beds_occupied = sum(h.beds_occupied for h in hostels)
    beds_maintenance = sum(h.beds_maintenance for h in hostels)
    beds_available = sum(h.beds_available for h in hostels)

    payments_confirmed = Payment.query.filter_by(status="confirmed").all()
    payments_pending = Payment.query.filter_by(status="pending").all()

    return {
        "occupancy": {
            "beds_total": beds_total,
            "beds_occupied": beds_occupied,
            "beds_available": beds_available,
            "beds_maintenance": beds_maintenance,
            "occupancy_rate": round(100.0 * beds_occupied / beds_total, 1) if beds_total else 0,
        },
        "allocations": {
            "active": Allocation.query.filter(Allocation.status.in_(("allocated", "checked_in"))).count(),
            "checked_in": Allocation.query.filter_by(status="checked_in").count(),
            "checked_out": Allocation.query.filter_by(status="checked_out").count(),
        },
        "applications": {
            "pending": Application.query.filter_by(status="pending").count(),
            "under_review": Application.query.filter_by(status="under_review").count(),
            "approved": Application.query.filter_by(status="approved").count(),
            "rejected": Application.query.filter_by(status="rejected").count(),
        },
        "payments": {
            "confirmed_total": round(sum(p.amount for p in payments_confirmed), 2),
            "confirmed_count": len(payments_confirmed),
            "pending_total": round(sum(p.amount for p in payments_pending), 2),
            "pending_count": len(payments_pending),
            "currency": "KSh",
        },
    }


def occupancy_rows():
    rows = []
    for h in Hostel.query.order_by(Hostel.name).all():
        rows.append(
            {
                "hostel": h.name,
                "rooms": h.rooms.count(),
                "beds_total": h.beds_total,
                "beds_occupied": h.beds_occupied,
                "beds_available": h.beds_available,
                "beds_maintenance": h.beds_maintenance,
                "occupancy_rate": h.occupancy_rate,
            }
        )
    return rows


def vacancy_rows():
    beds = Bed.query.filter_by(status="available").all()
    rows = {}
    for b in beds:
        key = f"{b.room.hostel.name} / Room {b.room.number}"
        rows.setdefault(key, []).append(b.bed_number)
    data = [{"location": k, "free_beds": len(v), "bed_numbers": ", ".join(v)} for k, v in rows.items()]
    return data, len(beds)


def payments_report():
    by_method = {}
    by_status = {}
    by_semester = {}
    for p in Payment.query.all():
        by_method.setdefault(p.method, {"count": 0, "total": 0, "currency": p.currency})
        by_method[p.method]["count"] += 1
        if p.status == "confirmed":
            by_method[p.method]["total"] += p.amount

        st = by_status.setdefault(p.status, {"count": 0, "total": 0})
        st["count"] += 1
        if p.status != "failed":
            st["total"] += p.amount

        sem = by_semester.setdefault(p.semester, {"count": 0, "confirmed_total": 0})
        sem["count"] += 1
        if p.status == "confirmed":
            sem["confirmed_total"] += p.amount

    return {"by_method": by_method, "by_status": by_status, "by_semester": by_semester}


def allocation_rows():
    return [
        {
            "student": a.student.user.full_name,
            "registration_no": a.student.registration_no or "",
            "hostel": a.bed.room.hostel.name,
            "room": a.bed.room.number,
            "bed": a.bed.bed_number,
            "status": a.status,
            "paid": a.paid,
            "allocated_at": a.allocated_at.date().isoformat() if a.allocated_at else "",
        }
        for a in Allocation.query.order_by(Allocation.allocated_at.desc()).all()
    ]


def unread_counts(user_id):
    unread = Notification.query.filter_by(user_id=user_id, is_read=False).count()
    return unread
