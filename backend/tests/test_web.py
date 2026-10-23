import io
import re

from app.extensions import db
from app.models import Hostel, Room, Bed, User

ADMIN = {"email": "admin@test.ac.ke", "password": "Admin@123"}


def _login(client, credentials):
    return client.post("/login", data=credentials, follow_redirects=False)


def test_login_logout_flow(client):
    res = _login(client, ADMIN)
    assert res.status_code == 302 and "/dashboard" in res.headers["Location"]

    res = client.get("/admin/dashboard", follow_redirects=False)
    assert res.status_code == 200

    res = client.get("/logout", follow_redirects=False)
    assert res.status_code == 302

    res = client.get("/admin/dashboard", follow_redirects=False)
    assert res.status_code == 302 and res.headers["Location"].endswith("/login")

    bad = _login(client, ADMIN | {"password": "wrongpass"})
    assert bad.status_code == 302 and bad.headers["Location"].endswith("/login")


def test_register_web_flow(client):
    res = client.post(
        "/register",
        data={"full_name": "Web User", "email": "webuser@test.ac.ke", "password": "Pass@123", "registration_no": "25/12", "year_of_study": "1"},
        follow_redirects=False,
    )
    assert res.status_code == 302 and "/my/dashboard" in res.headers["Location"]
    res = client.get("/my/dashboard")
    assert b"not verified yet" in res.data


def test_admin_manage_hostel_through_web(client):
    _login(client, ADMIN)

    res = client.post("/admin/hostels", data={"name": "Web Hall", "gender": "female", "location": "West"}, follow_redirects=False)
    assert res.status_code == 302
    with client.application.app_context():
        hostel_id = Hostel.query.filter_by(name="Web Hall").first().id

    res = client.post(f"/admin/hostels/{hostel_id}/rooms", data={"number": "101", "floor": "1", "bed_count": "3"}, follow_redirects=False)
    assert res.status_code == 302
    with client.application.app_context():
        assert Room.query.filter_by(hostel_id=hostel_id, number="101").first().beds.count() == 3

    res = client.get("/admin/hostels")
    assert b"Web Hall" in res.data


def test_student_profile_accepts_name_and_image_fields(client):
    client.post(
        "/register",
        data={"full_name": "Profile User", "email": "profile@test.ac.ke", "password": "Pass@123", "registration_no": "25/77"},
        follow_redirects=False,
    )
    user = User.query.filter_by(email="profile@test.ac.ke").first()
    assert user is not None

    res = client.post(
        "/my/profile",
        data={"full_name": "Updated Name", "profile_image_url": "https://example.com/avatar.png"},
        follow_redirects=False,
    )
    assert res.status_code == 302
    user = User.query.filter_by(email="profile@test.ac.ke").first()
    assert user.full_name == "Updated Name"
    assert user.profile_image == "https://example.com/avatar.png"


def test_admin_can_upload_hostel_image(client):
    _login(client, ADMIN)

    res = client.post(
        "/admin/hostels",
        data={
            "name": "Image Hall",
            "gender": "mixed",
            "location": "North Wing",
            "image_file": (io.BytesIO(b"fake-image"), "hall.png"),
        },
        content_type="multipart/form-data",
        follow_redirects=False,
    )
    assert res.status_code == 302
    with client.application.app_context():
        hostel = Hostel.query.filter_by(name="Image Hall").first()
        assert hostel is not None
        assert hostel.image_url and hostel.image_url.endswith("hall.png")


def test_admin_can_configure_mpesa_daraja_settings(client):
    _login(client, ADMIN)

    res = client.post(
        "/admin/payments/settings",
        data={
            "mpesa_enabled": "on",
            "mpesa_consumer_key": "consumer-key",
            "mpesa_consumer_secret": "consumer-secret",
            "mpesa_shortcode": "174379",
            "mpesa_passkey": "passkey-123",
            "mpesa_callback_url": "https://example.com/mpesa/callback",
            "mpesa_environment": "sandbox",
        },
        follow_redirects=False,
    )
    assert res.status_code == 302

    with client.application.app_context():
        from app.models import MpesaSettings

        settings = MpesaSettings.query.first()
        assert settings is not None
        assert settings.mpesa_enabled is True
        assert settings.mpesa_consumer_key == "consumer-key"
        assert settings.mpesa_shortcode == "174379"

    res = client.get("/admin/payments")
    assert b"Daraja" in res.data


def test_student_full_web_journey(client):
    client.post(
        "/register",
        data={"full_name": "Journey", "email": "journey@test.ac.ke", "password": "Pass@123", "registration_no": "25/34"},
        follow_redirects=False,
    )

    with client.application.app_context():
        student_id = User.query.filter_by(email="journey@test.ac.ke").first().student.id
        hostel = Hostel(name="J Hall", gender="female", location="East")
        db.session.add(hostel)
        db.session.flush()
        room = Room(hostel_id=hostel.id, number="201")
        db.session.add(room)
        db.session.flush()
        bed = Bed(room_id=room.id, bed_number="1")
        db.session.add(bed)
        db.session.commit()

    admin = client.application.test_client()
    _login(admin, ADMIN)

    res = client.post("/my/apply", data={"room_preference": "shared"}, follow_redirects=False)
    assert res.status_code == 302

    res = admin.post(f"/admin/students/{student_id}/verify", data={"action": "verify"}, follow_redirects=False)
    assert res.status_code == 302

    res = client.post("/my/apply", data={"room_preference": "shared", "notes": "web journey"}, follow_redirects=False)
    assert res.status_code == 302

    res = admin.get("/admin/applications")
    match = re.search(rb'name="application_id" value="(\d+)">.*?value="approve"', res.data, re.S)
    assert match, "approve button for pending application expected"
    app_id = match.group(1).decode()

    res = admin.post("/admin/applications", data={"application_id": app_id, "review_action": "approve"}, follow_redirects=False)
    assert res.status_code == 302

    res = admin.get("/admin/applications", query_string={"status": "approved"})
    match = re.search(rb'<option value="(\d+)">J Hall', res.data)
    assert match, "free bed offered for allocation expected"
    bed_id = match.group(1).decode()

    res = admin.post("/admin/applications", data={"application_id": app_id, "allocate_action": "allocate", "bed_id": bed_id}, follow_redirects=False)
    assert res.status_code == 302

    res = client.get("/my/dashboard")
    assert b"J Hall" in res.data

    res = client.get("/my/payments")
    assert b"Bank transfer" not in res.data
    assert b"Cash" not in res.data
    assert b"Card" not in res.data
    assert b"M-Pesa" in res.data
    match = re.search(rb'name="allocation_id".*?<option value="(\d+)"', res.data, re.S)
    assert match, "allocation offered in payment form expected"
    allocation_id = match.group(1).decode()

    res = client.post("/my/payments", data={"amount": "14500", "method": "mpesa", "phone_number": "254712345678", "allocation_id": allocation_id, "semester": "2026 Semester 1"}, follow_redirects=False)
    assert res.status_code == 302

    res = admin.get("/admin/payments")
    match = re.search(rb'name="payment_id" value="(\d+)">.*?value="confirm"', res.data, re.S)
    assert match, "pending payment with confirm button expected"
    payment_id = match.group(1).decode()

    res = admin.post("/admin/payments", data={"payment_id": payment_id, "payment_action": "confirm"}, follow_redirects=False)
    assert res.status_code == 302

    res = client.get("/my/dashboard")
    assert b"confirmed" in res.data
