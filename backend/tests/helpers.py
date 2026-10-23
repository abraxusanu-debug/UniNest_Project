"""Shared helpers: create a hostel + bed, verify student, create+approve application, allocate, return allocation id."""

from app.extensions import db
from app.models import Hostel, Room, Bed
from tests.conftest import A


def seed_hostel_and_bed(client, app, tokens):
    with app.app_context():
        hostel = Hostel(name="Test Hall", gender="male", location="Campus")
        db.session.add(hostel)
        db.session.flush()
        room = Room(hostel_id=hostel.id, number="101", floor=1, room_type="shared")
        db.session.add(room)
        db.session.flush()
        bed = Bed(room_id=room.id, bed_number="1")
        db.session.add(bed)
        db.session.commit()
        hostel_id, bed_id = hostel.id, bed.id

    me = client.get("/api/students/me", headers=A(tokens["student"])).json
    client.post(f"/api/students/{me['id']}/verify", headers=A(tokens["admin"]), json={"action": "verify"})
    app_row = client.post("/api/applications", headers=A(tokens["student"]), json={"room_preference": "any"})
    client.post(f"/api/applications/{app_row.json['id']}/review", headers=A(tokens["admin"]), json={"action": "approve"})
    alloc = client.post(
        "/api/allocations",
        headers=A(tokens["admin"]),
        json={"application_id": app_row.json["id"], "bed_id": bed_id},
    )
    assert alloc.status_code == 201, alloc.json
    return alloc.json["id"]
