from flask import Blueprint, jsonify, request

from app.services import hostel_service
from app.services.errors import ServiceError
from app.utils import role_required

bp = Blueprint("hostels", __name__, url_prefix="/api/hostels")


@bp.get("")
def list_hostels():
    hostels = hostel_service.list_hostels()
    return jsonify({"hostels": [h.to_dict() for h in hostels], "count": len(hostels)})


@bp.get("/<int:hostel_id>")
def get_hostel(hostel_id):
    try:
        hostel, rooms = hostel_service.get_hostel(hostel_id, include_beds=request.args.get("beds") == "1")
        data = hostel.to_dict()
        data["rooms"] = rooms
        return jsonify(data)
    except ServiceError as e:
        return jsonify({"error": e.kind, "message": e.message}), e.status


@bp.post("")
@role_required("admin")
def create_hostel():
    data = request.get_json(silent=True) or {}
    try:
        hostel = hostel_service.create_hostel(data.get("name"), data.get("gender", "mixed"), data.get("location"), data.get("description"))
        return jsonify(hostel.to_dict()), 201
    except ServiceError as e:
        return jsonify({"error": e.kind, "message": e.message}), e.status


@bp.put("/<int:hostel_id>")
@role_required("admin")
def update_hostel(hostel_id):
    try:
        hostel = hostel_service.update_hostel(hostel_id, request.get_json(silent=True) or {})
        return jsonify(hostel.to_dict())
    except ServiceError as e:
        return jsonify({"error": e.kind, "message": e.message}), e.status


@bp.delete("/<int:hostel_id>")
@role_required("admin")
def delete_hostel(hostel_id):
    try:
        hostel_service.delete_hostel(hostel_id)
        return jsonify({"message": "hostel deleted"})
    except ServiceError as e:
        return jsonify({"error": e.kind, "message": e.message}), e.status


@bp.post("/<int:hostel_id>/rooms")
@role_required("admin")
def create_room(hostel_id):
    data = request.get_json(silent=True) or {}
    try:
        room = hostel_service.create_room(
            hostel_id,
            data.get("number"),
            data.get("floor"),
            data.get("room_type", "shared"),
            data.get("bed_count"),
        )
        return jsonify(room.to_dict(include_beds=True)), 201
    except ServiceError as e:
        return jsonify({"error": e.kind, "message": e.message}), e.status


@bp.put("/rooms/<int:room_id>")
@role_required("admin")
def update_room(room_id):
    try:
        room = hostel_service.update_room(room_id, request.get_json(silent=True) or {})
        return jsonify(room.to_dict(include_beds=True))
    except ServiceError as e:
        return jsonify({"error": e.kind, "message": e.message}), e.status


@bp.delete("/rooms/<int:room_id>")
@role_required("admin")
def delete_room(room_id):
    try:
        hostel_service.delete_room(room_id)
        return jsonify({"message": "room deleted"})
    except ServiceError as e:
        return jsonify({"error": e.kind, "message": e.message}), e.status


@bp.post("/rooms/<int:room_id>/beds")
@role_required("admin")
def add_beds(room_id):
    data = request.get_json(silent=True) or {}
    try:
        created = hostel_service.add_beds(room_id, data.get("count", 1))
        return jsonify({"created": len(created), "beds": [b.to_dict() for b in created]}), 201
    except ServiceError as e:
        return jsonify({"error": e.kind, "message": e.message}), e.status


@bp.put("/beds/<int:bed_id>")
@role_required("admin")
def update_bed(bed_id):
    try:
        bed = hostel_service.update_bed(bed_id, request.get_json(silent=True) or {})
        return jsonify(bed.to_dict())
    except ServiceError as e:
        return jsonify({"error": e.kind, "message": e.message}), e.status


@bp.delete("/beds/<int:bed_id>")
@role_required("admin")
def delete_bed(bed_id):
    try:
        hostel_service.delete_bed(bed_id)
        return jsonify({"message": "bed deleted"})
    except ServiceError as e:
        return jsonify({"error": e.kind, "message": e.message}), e.status


@bp.get("/availability/overview")
def availability():
    return jsonify({"hostels": hostel_service.availability_overview()})
