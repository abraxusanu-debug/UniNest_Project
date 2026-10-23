from datetime import datetime

from app.extensions import db
from sqlalchemy.orm import validates

GENDERS = ("male", "female", "mixed")
BED_STATUSES = ("available", "occupied", "maintenance")


class Hostel(db.Model):
    __tablename__ = "hostels"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    gender = db.Column(db.String(10), nullable=False, default="mixed")
    location = db.Column(db.String(120))
    description = db.Column(db.String(255))
    image_url = db.Column(db.String(500))
    amenities = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    rooms = db.relationship("Room", back_populates="hostel", cascade="all, delete-orphan", lazy="dynamic")

    @property
    def beds_total(self):
        return sum(r.beds_total for r in self.rooms)

    @property
    def beds_occupied(self):
        return sum(r.beds_occupied for r in self.rooms)

    @property
    def beds_available(self):
        return self.beds_total - self.beds_occupied - self.beds_maintenance

    @property
    def beds_maintenance(self):
        return sum(r.beds_maintenance for r in self.rooms)

    @property
    def occupancy_rate(self):
        if self.beds_total == 0:
            return 0
        return round(100.0 * self.beds_occupied / self.beds_total, 1)

    @property
    def amenity_list(self):
        if not self.amenities:
            return []
        values = self.amenities.replace("\n", ",").split(",")
        cleaned = []
        for item in values:
            item = item.strip()
            if item and item not in cleaned:
                cleaned.append(item)
        return cleaned

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "gender": self.gender,
            "location": self.location,
            "description": self.description,
            "image_url": self.image_url,
            "amenities": self.amenity_list,
            "rooms_count": self.rooms.count() if self.rooms else 0,
            "beds_total": self.beds_total,
            "beds_occupied": self.beds_occupied,
            "beds_available": self.beds_available,
            "beds_maintenance": self.beds_maintenance,
            "occupancy_rate": self.occupancy_rate,
        }


class Room(db.Model):
    __tablename__ = "rooms"

    id = db.Column(db.Integer, primary_key=True)
    hostel_id = db.Column(db.Integer, db.ForeignKey("hostels.id"), nullable=False)
    number = db.Column(db.String(20), nullable=False)
    floor = db.Column(db.Integer)
    room_type = db.Column(db.String(20), default="shared")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    hostel = db.relationship("Hostel", back_populates="rooms")
    beds = db.relationship("Bed", back_populates="room", cascade="all, delete-orphan", lazy="dynamic")

    __table_args__ = (db.UniqueConstraint("hostel_id", "number", name="uq_room_number_in_hostel"),)

    @property
    def beds_total(self):
        return self.beds.count()

    @property
    def beds_occupied(self):
        return self.beds.filter_by(status="occupied").count()

    @property
    def beds_maintenance(self):
        return self.beds.filter_by(status="maintenance").count()

    @property
    def beds_available(self):
        return self.beds.filter_by(status="available").count()

    def to_dict(self, include_beds=False):
        data = {
            "id": self.id,
            "hostel_id": self.hostel_id,
            "hostel_name": self.hostel.name,
            "number": self.number,
            "floor": self.floor,
            "room_type": self.room_type,
            "beds_total": self.beds_total,
            "beds_occupied": self.beds_occupied,
            "beds_available": self.beds_available,
            "beds_maintenance": self.beds_maintenance,
        }
        if include_beds:
            data["beds"] = [b.to_dict() for b in self.beds.order_by(Bed.bed_number)]
        return data


class Bed(db.Model):
    __tablename__ = "beds"

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id"), nullable=False)
    bed_number = db.Column(db.String(20), nullable=False, default="1")
    status = db.Column(db.String(20), nullable=False, default="available")

    room = db.relationship("Room", back_populates="beds")

    @validates("status")
    def validate_status(self, key, value):
        if value not in BED_STATUSES:
            raise ValueError(f"invalid bed status: {value}")
        return value

    def to_dict(self):
        return {
            "id": self.id,
            "room_id": self.room_id,
            "room_number": self.room.number if self.room else None,
            "hostel": self.room.hostel.name if self.room else None,
            "bed_number": self.bed_number,
            "status": self.status,
        }
