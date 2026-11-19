from tests.conftest import A


def test_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200 and res.json["service"] == "uninest"


def test_register_login_me(client):
    res = client.post(
        "/api/auth/register",
        json={"email": "z@t.ac.ke", "password": "Pass@123", "full_name": "Z X", "registration_no": "25/1"},
    )
    assert res.status_code == 201
    assert res.json["user"]["verification_status"] == "unverified"

    dup = client.post(
        "/api/auth/register",
        json={"email": "z@t.ac.ke", "password": "Pass@123", "full_name": "Z X"},
    )
    assert dup.status_code == 409

    login = client.post("/api/auth/login", json={"email": "z@t.ac.ke", "password": "Pass@123"})
    token = login.json["token"]
    me = client.get("/api/auth/me", headers=A(token))
    assert me.status_code == 200 and me.json["email"] == "z@t.ac.ke"

    bad = client.post("/api/auth/login", json={"email": "z@t.ac.ke", "password": "nope"})
    assert bad.status_code == 401


def test_application_flow_requires_verification(client, tokens):
    res = client.post("/api/applications", headers=A(tokens["student"]), json={"room_preference": "shared"})
    assert res.status_code == 403

    me = client.get("/api/students/me", headers=A(tokens["student"])).json
    verify = client.post(f"/api/students/{me['id']}/verify", headers=A(tokens["admin"]), json={"action": "verify"})
    assert verify.json["verification_status"] == "verified"

    app_row = client.post("/api/applications", headers=A(tokens["student"]), json={"room_preference": "shared"})
    assert app_row.status_code == 201 and app_row.json["status"] == "pending"

    dup = client.post("/api/applications", headers=A(tokens["student"]), json={})
    assert dup.status_code == 409

    aid = app_row.json["id"]
    reject_student_view = client.get(f"/api/applications/{aid}", headers=A(tokens["student"]))
    assert reject_student_view.status_code == 200

    approve = client.post(f"/api/applications/{aid}/review", headers=A(tokens["admin"]), json={"action": "approve"})
    assert approve.status_code == 200 and approve.json["status"] == "approved"

    forbidden = client.post(f"/api/applications/{aid}/review", headers=A(tokens["student"]), json={"action": "approve"})
    assert forbidden.status_code == 403


def test_allocation_bed_lifecycle(client, app, tokens):
    from tests.helpers import seed_hostel_and_bed

    app_id = seed_hostel_and_bed(client, app, tokens)

    list_alloc = client.get("/api/allocations", headers=A(tokens["student"]))
    assert list_alloc.status_code == 200
    alloc_id = list_alloc.json["allocations"][0]["id"]
    detail = client.get(f"/api/allocations/{alloc_id}", headers=A(tokens["student"]))
    assert detail.status_code == 200

    checkin = client.post(f"/api/allocations/{alloc_id}/check-in", headers=A(tokens["admin"]))
    assert checkin.status_code == 200 and checkin.json["status"] == "checked_in"

    checkout = client.post(f"/api/allocations/{alloc_id}/check-out", headers=A(tokens["admin"]))
    assert checkout.status_code == 200 and checkout.json["status"] == "checked_out"


def test_payment_confirm_updates_allocation(client, app, tokens):
    from tests.helpers import seed_hostel_and_bed

    alloc_id = seed_hostel_and_bed(client, app, tokens)

    pay = client.post(
        "/api/payments",
        headers=A(tokens["student"]),
        json={"amount": 1000, "method": "mpesa", "allocation_id": alloc_id},
    )
    assert pay.status_code == 201 and pay.json["status"] == "pending"

    confirm = client.post(f"/api/payments/{pay.json['id']}/confirm", headers=A(tokens["admin"]))
    assert confirm.status_code == 200 and confirm.json["status"] == "confirmed"

    alloc = client.get(f"/api/allocations/{alloc_id}", headers=A(tokens["student"])).json
    assert alloc["paid"] is True and alloc["accommodation_confirmed"] is True


def test_partial_payment_does_not_confirm_accommodation(client, app, tokens):
    from decimal import Decimal
    from tests.helpers import seed_hostel_and_bed
    from app.models import MpesaSettings
    from app.extensions import db

    alloc_id = seed_hostel_and_bed(client, app, tokens)
    with app.app_context():
        settings = MpesaSettings.get_or_create()
        settings.accommodation_required_amount = Decimal("14500.00")
        db.session.commit()

    pay = client.post(
        "/api/payments",
        headers=A(tokens["student"]),
        json={"amount": 1000, "method": "mpesa", "allocation_id": alloc_id},
    )
    confirm = client.post(f"/api/payments/{pay.json['id']}/confirm", headers=A(tokens["admin"]))
    assert confirm.status_code == 200

    alloc = client.get(f"/api/allocations/{alloc_id}", headers=A(tokens["student"])).json
    assert alloc["paid"] is False
    assert alloc["accommodation_confirmed"] is False
    assert confirm.json["status"] == "confirmed"


def test_rejected_payment_has_processing_audit(client, app, tokens):
    from tests.helpers import seed_hostel_and_bed

    alloc_id = seed_hostel_and_bed(client, app, tokens)
    pay = client.post(
        "/api/payments",
        headers=A(tokens["student"]),
        json={"amount": 1000, "method": "mpesa", "allocation_id": alloc_id},
    )
    reject = client.post(f"/api/payments/{pay.json['id']}/fail", headers=A(tokens["admin"]))
    assert reject.status_code == 200
    assert reject.json["status"] == "failed"
    assert reject.json["confirmed_at"] is not None


def test_password_and_notification_email_policy(client, monkeypatch):
    sent = []

    from app.services import email_service

    monkeypatch.setattr(
        email_service,
        "send_email",
        lambda subject, body, recipient, **kwargs: sent.append((subject, body, recipient)) or True,
    )

    short = client.post(
        "/api/auth/register",
        json={"email": "short@test.ac.ke", "password": "Short1", "full_name": "Short Password"},
    )
    assert short.status_code == 400

    created = client.post(
        "/api/auth/register",
        json={"email": "email@test.ac.ke", "password": "Strong@123", "full_name": "Email User"},
    )
    assert created.status_code == 201

    login = client.post(
        "/api/auth/login",
        json={"email": "email@test.ac.ke", "password": "Strong@123"},
    )
    assert login.status_code == 200

    subjects = [item[0] for item in sent]
    assert "Welcome to UniNest" in subjects
    assert "UniNest login alert" in subjects
    assert all("password_hash" not in item[1] for item in sent)
    assert all("KSh" not in item[1] for item in sent)


def test_reports_and_guards(client, tokens):
    ok = client.get("/api/reports/summary", headers=A(tokens["admin"]))
    assert ok.status_code == 200 and "occupancy" in ok.json

    denied = client.get("/api/reports/summary", headers=A(tokens["student"]))
    assert denied.status_code == 403
