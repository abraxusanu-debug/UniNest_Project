import csv
import io

from flask import Blueprint, Response, jsonify

from app.services import report_service
from app.utils import is_staff

bp = Blueprint("reports", __name__, url_prefix="/api/reports")


def _forbidden():
    return jsonify({"error": "forbidden", "message": "insufficient permissions"}), 403


@bp.get("/summary")
def summary():
    if not is_staff():
        return _forbidden()
    return jsonify(report_service.summary())


@bp.get("/occupancy")
def occupancy_report():
    if not is_staff():
        return _forbidden()
    return jsonify({"report": "occupancy", "rows": report_service.occupancy_rows()})


@bp.get("/vacancies")
def vacancies_report():
    if not is_staff():
        return _forbidden()
    rows, total_free = report_service.vacancy_rows()
    return jsonify({"report": "vacancies", "rows": rows, "total_free_beds": total_free})


@bp.get("/payments")
def payments_report():
    if not is_staff():
        return _forbidden()
    return jsonify({"report": "payments", **report_service.payments_report()})


def _csv_response(rows, headers, filename):
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=headers)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return Response(out.getvalue(), mimetype="text/csv", headers={"Content-Disposition": f"attachment; filename={filename}"})


@bp.get("/occupancy.csv")
def occupancy_csv():
    if not is_staff():
        return _forbidden()
    rows = report_service.occupancy_rows()
    mapped = [
        {
            "Hostel": r["hostel"],
            "Rooms": r["rooms"],
            "Beds Total": r["beds_total"],
            "Beds Occupied": r["beds_occupied"],
            "Beds Available": r["beds_available"],
            "Occupancy %": r["occupancy_rate"],
        }
        for r in rows
    ]
    return _csv_response(mapped, ["Hostel", "Rooms", "Beds Total", "Beds Occupied", "Beds Available", "Occupancy %"], "occupancy.csv")


@bp.get("/allocations.csv")
def allocations_csv():
    if not is_staff():
        return _forbidden()
    mapped = [
        {
            "Student": r["student"],
            "Registration No": r["registration_no"],
            "Hostel": r["hostel"],
            "Room": r["room"],
            "Bed": r["bed"],
            "Status": r["status"],
            "Paid": r["paid"],
            "Allocated At": r["allocated_at"],
        }
        for r in report_service.allocation_rows()
    ]
    return _csv_response(mapped, ["Student", "Registration No", "Hostel", "Room", "Bed", "Status", "Paid", "Allocated At"], "allocations.csv")
