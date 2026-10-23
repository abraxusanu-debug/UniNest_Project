from app.extensions import db
from app.models import Hostel, Room, Bed
from app.services.errors import Conflict, NotFound


def _normalize_amenities(value):
    if value is None:
        return ""
    if isinstance(value, (list, tuple, set)):
        items = value
    else:
        items = str(value).replace("\n", ",").split(",")
    cleaned = []
    for item in items:
        item = str(item).strip()
        if item and item not in cleaned:
            cleaned.append(item)
    return ", ".join(cleaned)


def list_hostels():
    return Hostel.query.order_by(Hostel.name).all()


def get_hostel(hostel_id, include_beds=False):
    hostel = db.session.get(Hostel, hostel_id)
    if not hostel:
        raise NotFound("hostel not found")
    return hostel, [r.to_dict(include_beds=include_beds) for r in hostel.rooms.order_by(Room.number)]


def create_hostel(name, gender="mixed", location=None, description=None, image_url=None, amenities=None):
    if not name:
        raise Conflict("hostel name is required")
    if Hostel.query.filter_by(name=name).first():
        raise Conflict("a hostel with this name already exists")
    if gender not in ("male", "female", "mixed"):
        raise Conflict("gender must be male, female or mixed")

    hostel = Hostel(
        name=name.strip(),
        gender=gender,
        location=location.strip() if location else None,
        description=description.strip() if description else None,
        image_url=image_url.strip() if image_url else None,
        amenities=_normalize_amenities(amenities),
    )
    db.session.add(hostel)
    db.session.commit()
    return hostel


def update_hostel(hostel_id, data):
    hostel = db.session.get(Hostel, hostel_id)
    if not hostel:
        raise NotFound("hostel not found")
    if data.get("gender") and data["gender"] not in ("male", "female", "mixed"):
        raise Conflict("invalid gender")
    for field in ("name", "gender", "location", "description", "image_url"):
        if field in data:
            setattr(hostel, field, data[field])
    if "amenities" in data:
        hostel.amenities = _normalize_amenities(data["amenities"])
    db.session.commit()
    return hostel


def delete_hostel(hostel_id):
    hostel = db.session.get(Hostel, hostel_id)
    if not hostel:
        raise NotFound("hostel not found")
    if hostel.beds_occupied > 0:
        raise Conflict("cannot delete a hostel with occupied beds")
    db.session.delete(hostel)
    db.session.commit()


def create_room(hostel_id, number, floor=None, room_type="shared", bed_count=None):
    hostel = db.session.get(Hostel, hostel_id)
    if not hostel:
        raise NotFound("hostel not found")
    if not number:
        raise Conflict("room number is required")
    number = str(number).strip()
    if Room.query.filter_by(hostel_id=hostel_id, number=number).first():
        raise Conflict("this room number already exists in the hostel")
    if room_type not in ("shared", "single"):
        room_type = "shared"

    room = Room(hostel_id=hostel_id, number=number, floor=floor, room_type=room_type)
    db.session.add(room)
    db.session.flush()

    if isinstance(bed_count, int) and 0 < bed_count <= 30:
        existing = {b.bed_number for b in room.beds}
        n = 1
        while len(existing) < bed_count and n <= 100:
            label = str(n)
            if label not in existing:
                db.session.add(Bed(room_id=room.id, bed_number=label))
                existing.add(label)
            n += 1

    db.session.commit()
    return room


def update_room(room_id, data):
    room = db.session.get(Room, room_id)
    if not room:
        raise NotFound("room not found")
    for field in ("number", "floor", "room_type"):
        if field in data:
            setattr(room, field, data[field])
    db.session.commit()
    return room


def delete_room(room_id):
    room = db.session.get(Room, room_id)
    if not room:
        raise NotFound("room not found")
    if room.beds_occupied > 0:
        raise Conflict("cannot delete a room with occupied beds")
    db.session.delete(room)
    db.session.commit()


def add_beds(room_id, count=1):
    room = db.session.get(Room, room_id)
    if not room:
        raise NotFound("room not found")
    if not isinstance(count, int) or count < 1 or count > 30:
        raise Conflict("count must be an integer between 1 and 30")

    existing = {b.bed_number for b in room.beds}
    created = []
    n = 1
    while len(existing) < 100 and n <= 100:
        label = str(n)
        if label not in existing:
            bed = Bed(room_id=room_id, bed_number=label)
            db.session.add(bed)
            created.append(bed)
            existing.add(label)
            if len(created) >= count:
                break
        n += 1
    db.session.commit()
    return created


def update_bed(bed_id, data):
    bed = db.session.get(Bed, bed_id)
    if not bed:
        raise NotFound("bed not found")
    if bed.status == "occupied" and data.get("status", "occupied") != "occupied":
        raise Conflict("bed is allocated to a student; release the allocation first")
    if not data.get("status") and not data.get("bed_number"):
        raise Conflict("nothing to update")
    if data.get("bed_number"):
        bed.bed_number = str(data["bed_number"])
    if data.get("status") in ("available", "maintenance"):
        bed.status = data["status"]
    db.session.commit()
    return bed


def delete_bed(bed_id):
    bed = db.session.get(Bed, bed_id)
    if not bed:
        raise NotFound("bed not found")
    if bed.status == "occupied":
        raise Conflict("bed is allocated to a student; release the allocation first")
    db.session.delete(bed)
    db.session.commit()


def availability_overview():
    result = []
    for h in list_hostels():
        hostel_data = h.to_dict()
        hostel_data["rooms"] = [r.to_dict(include_beds=True) for r in h.rooms.order_by(Room.number)]
        result.append(hostel_data)
    return result
