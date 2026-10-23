import base64
import json
import secrets
from datetime import datetime
from urllib import error, request

from app.extensions import db
from app.models import Payment, Allocation, Student, MpesaSettings
from app.services.errors import Conflict, NotFound
from app.services.common import notify


def make_reference():
    return "UNI-" + secrets.token_hex(5).upper()


def normalize_phone_number(phone_number):
    value = (phone_number or "").strip().replace(" ", "")
    if not value:
        return ""
    value = value.replace("+", "")
    if value.startswith("0"):
        value = "254" + value[1:]
    return value


def _mpesa_token(settings):
    if not settings or not settings.mpesa_consumer_key or not settings.mpesa_consumer_secret:
        raise Conflict("Daraja credentials are not configured")

    auth = base64.b64encode(f"{settings.mpesa_consumer_key}:{settings.mpesa_consumer_secret}".encode()).decode()
    endpoint = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    if settings.mpesa_environment == "production":
        endpoint = "https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"

    req = request.Request(endpoint, headers={"Authorization": f"Basic {auth}", "Content-Type": "application/json"}, method="GET")
    with request.urlopen(req, timeout=20) as response:
        payload = json.loads(response.read().decode())
        return payload.get("access_token")


def _mpesa_callback_url(settings):
    if settings.mpesa_callback_url:
        return settings.mpesa_callback_url
    return "https://example.com/mpesa/callback"


def _send_stk_push(payment, settings, phone_number):
    if not phone_number:
        raise Conflict("a phone number is required for M-Pesa payments")
    if not settings.mpesa_shortcode or not settings.mpesa_passkey:
        raise Conflict("Daraja shortcode and passkey are not configured")

    normalized_phone = normalize_phone_number(phone_number)
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    password = base64.b64encode(f"{settings.mpesa_shortcode}{settings.mpesa_passkey}{timestamp}".encode()).decode()
    payload = {
        "BusinessShortCode": settings.mpesa_shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": str(int(payment.amount)),
        "PartyA": normalized_phone,
        "PartyB": settings.mpesa_shortcode,
        "PhoneNumber": normalized_phone,
        "CallBackURL": _mpesa_callback_url(settings),
        "AccountReference": payment.reference,
        "TransactionDesc": payment.description or "Hostel accommodation fee",
    }

    endpoint = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    if settings.mpesa_environment == "production":
        endpoint = "https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest"

    token = _mpesa_token(settings)
    api_request = request.Request(
        endpoint,
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    with request.urlopen(api_request, timeout=30) as response:
        response_payload = json.loads(response.read().decode())
        return response_payload


def record_payment(student_id, amount, method="mpesa", allocation_id=None, semester=None, description=None, phone_number=None):
    if amount is None:
        raise Conflict("amount is required")
    try:
        amount = float(amount)
        if amount <= 0:
            raise ValueError
    except (TypeError, ValueError):
        raise Conflict("amount must be a positive number") from None

    if method != "mpesa":
        raise Conflict("only M-Pesa is supported for accommodation payments")

    method = "mpesa"

    if allocation_id:
        allocation = db.session.get(Allocation, allocation_id)
        if not allocation:
            raise NotFound("allocation not found")
        if allocation.student_id != student_id:
            raise Conflict("allocation does not belong to this student")

    payment = Payment(
        reference=make_reference(),
        student_id=student_id,
        allocation_id=allocation_id,
        amount=round(amount, 2),
        method=method,
        phone_number=(phone_number or "").strip() or None,
        semester=semester or "2026 Semester 1",
        description=description or "Hostel accommodation fee",
        status="pending",
    )
    db.session.add(payment)
    db.session.commit()
    return payment


def initiate_mpesa_payment(payment_id, phone_number=None, settings=None):
    payment = db.session.get(Payment, payment_id)
    if not payment:
        raise NotFound("payment not found")

    if phone_number:
        payment.phone_number = str(phone_number).strip() or None

    if payment.method != "mpesa":
        return payment

    settings = settings or MpesaSettings.get_or_create()
    configured = (
        settings.mpesa_enabled
        and settings.mpesa_consumer_key
        and settings.mpesa_consumer_secret
        and settings.mpesa_shortcode
        and settings.mpesa_passkey
    )

    if not configured:
        payment.status = "pending"
        db.session.commit()
        return payment

    try:
        response = _send_stk_push(payment, settings, payment.phone_number or phone_number)
    except (error.URLError, error.HTTPError, ValueError) as exc:
        payment.status = "pending"
        db.session.commit()
        return payment

    if response.get("ResponseCode") == "0":
        payment.status = "confirmed"
        payment.confirmed_at = datetime.utcnow()
        if payment.allocation_id:
            allocation = db.session.get(Allocation, payment.allocation_id)
            if allocation and allocation.status in ("allocated", "checked_in"):
                allocation.paid = True
                allocation.accommodation_confirmed = True
        notify(
            payment.student.user_id,
            "payment",
            "M-Pesa payment confirmed",
            f"Your payment of KSh {payment.amount:.2f} to {payment.phone_number or 'your registered number'} was received and settled automatically.",
        )
        db.session.commit()
        return payment

    payment.status = "pending"
    db.session.commit()
    return payment


def get_payment(payment_id):
    payment = db.session.get(Payment, payment_id)
    if not payment:
        raise NotFound("payment not found")
    return payment


def list_payments(student_id=None, status=None):
    query = Payment.query
    if student_id:
        query = query.filter(Payment.student_id == student_id)
    if status:
        query = query.filter(Payment.status == status)
    return query.order_by(Payment.created_at.desc()).all()


def confirm(payment_id, admin_id):
    payment = db.session.get(Payment, payment_id)
    if not payment:
        raise NotFound("payment not found")
    if payment.status != "pending":
        raise Conflict(f"payment is already {payment.status}")

    payment.status = "confirmed"
    payment.confirmed_by = admin_id
    payment.confirmed_at = datetime.utcnow()

    if payment.allocation_id:
        allocation = db.session.get(Allocation, payment.allocation_id)
        if allocation and allocation.status in ("allocated", "checked_in"):
            allocation.paid = True
            allocation.accommodation_confirmed = True

    notify(
        payment.student.user_id,
        "payment",
        "Payment confirmed",
        f"Payment {payment.reference} of {payment.currency} {payment.amount:.2f} has been confirmed. Accommodation confirmed.",
    )
    db.session.commit()
    return payment


def fail(payment_id, admin_id):
    payment = db.session.get(Payment, payment_id)
    if not payment:
        raise NotFound("payment not found")
    if payment.status != "pending":
        raise Conflict(f"payment is already {payment.status}")
    payment.status = "failed"
    payment.confirmed_by = admin_id
    notify(payment.student.user_id, "payment", "Payment not accepted", f"Payment {payment.reference} was not accepted. Please contact the hostel office.")
    db.session.commit()
    return payment
