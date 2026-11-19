# UniNest Presentation Trainer Guide

**Prepared for:** Final project presentation and system demonstration
**Project:** Design and Development of a University Hostel Management System
**Presenter:** Victor Ndirangu (25/03338)
**Date:** 19 November 2026

## 1. Presentation objective

The presentation demonstrates how UniNest replaces fragmented hostel records with one role-based system covering registration, verification, applications, allocations, payments, maintenance, notifications, and reports.

The presentation should establish:

1. the operational problem addressed;
2. the system architecture and role model;
3. the complete student and administrator workflows;
4. the integrity and security controls; and
5. the implemented test evidence.

## 2. Recommended timing

| Section | Time |
|---|---:|
| Introduction and problem | 1 minute |
| Objectives and architecture | 2 minutes |
| Student workflow | 3 minutes |
| Administrator workflow | 4 minutes |
| Payments, maintenance, and reports | 3 minutes |
| Testing and conclusion | 2 minutes |

**Total:** 15 minutes

## 3. Opening statement

UniNest is a centralized university hostel management system. It moves accommodation work from separate forms and spreadsheets into a shared platform where students submit and track applications, the hostel office verifies students and manages allocations, and university management views operational reports.

## 4. System overview

The system is available as a server-rendered web interface and a JSON REST API. Both interfaces share the same Flask service layer, SQLAlchemy models, validation rules, and database. The web interface uses session authentication, while the API uses JWT authentication.

The main roles are:

- **Student:** register, maintain permitted profile details, apply, withdraw pending applications, record payments, request maintenance, and receive updates;
- **Administrator:** verify students, manage hostels and rooms, approve applications, allocate beds, confirm payments, process maintenance, and generate reports;
- **Management:** view occupancy, applications, allocations, payment summaries, and operational reports without modifying records;
- **Maintenance:** view and resolve assigned maintenance requests.

## 5. Technical demonstration setup

Run the application from the project directory:

```bash
cd backend
python3 -m pip install -r requirements.txt
python3 -m app.seed
python3 run.py
```

Open `http://127.0.0.1:5001` in a browser.

Test accounts are documented in the repository README. Test credentials should not be repeated on the sign-in page.

## 6. Student presentation flow

### 6.1 Registration

1. Open the registration page.
2. Create a student account with the required personal and enrolment details.
3. Explain that passwords must contain at least eight characters and are stored as hashes.
4. Show that a successful account is logged in or directed to email verification according to site settings.

### 6.2 Verification gate

1. Sign in as an administrator.
2. Open the student queue.
3. Verify a student who is waiting for verification.
4. Explain that the student cannot submit a hostel application until verification is complete.

### 6.3 Application

1. Sign in as the verified student.
2. Open the application form.
3. Choose a preferred hostel and room type, then submit.
4. Show the application status and in-app notification.

## 7. Administrator presentation flow

### 7.1 Application review

1. Open the applications queue.
2. Move the application to under review.
3. Approve or reject the application and add review notes.
4. Explain that an approved application is eligible for bed allocation.

### 7.2 Bed allocation

1. Open the approved application.
2. Select an available bed.
3. Allocate the bed and demonstrate the status change.
4. Explain that UniNest prevents occupied-bed allocation and duplicate active allocations.

### 7.3 Check-in and check-out

1. Record check-in after the student arrives.
2. Record check-out at the end of the residence period.
3. Show that check-out frees the bed and completes the application.

## 8. Payment demonstration

1. Sign in as the student and open Payments.
2. Submit a payment record linked to the allocation.
3. Sign in as an administrator and open the payment queue.
4. Confirm or reject the payment.
5. Explain that confirmation requires the configured accommodation required amount and the cumulative confirmed amount for the allocation.

The demonstration should distinguish between an incomplete payment and a payment that is sufficient for accommodation confirmation.

## 9. Maintenance demonstration

1. Submit a maintenance request from the student account.
2. Show the submitted status and notification.
3. Open the maintenance queue as an administrator or maintenance worker.
4. Move the request to in progress and resolve it with a note.
5. Explain that resolved requests remain closed and visible for audit purposes.

## 10. Reports and management

Demonstrate:

- occupancy by hostel;
- available-bed lists;
- payment totals by method, semester, and status;
- allocation registers; and
- CSV downloads.

Explain that management has read-only operational access and cannot modify core records or view protected account fields.

## 11. Integrity and security talking points

- Registration numbers and emails are validated as unique identifiers.
- Verified registration-number changes reset hostel verification.
- Passwords use hashed storage and a minimum of eight characters.
- Five failed login attempts trigger a fifteen-minute lockout.
- Web forms use CSRF protection.
- API routes use JWT and role checks.
- Application, allocation, payment, and maintenance status transitions are controlled by service rules.
- Hostel and room deletion are blocked when occupied or linked to historical records.
- Payment amounts use decimal precision.

## 12. Testing evidence

The automated test suite covers:

- registration and login;
- verification gates;
- application and allocation lifecycles;
- payment confirmation and rejection;
- maintenance workflows;
- notification and report behaviour;
- role guards and web journeys.

State the verified result from the final test run rather than estimating test coverage.

## 13. Presentation close

Conclude with the complete operational journey:

**Register → verify → apply → review → allocate → check-in → pay → confirm → maintain → report → check-out**

The system provides one coordinated record of accommodation activity, with role-based access and explicit status transitions.

## 14. Question preparation

### Why use Flask?

Flask provides a lightweight application framework suitable for the server-rendered interface and REST API, with SQLAlchemy used for data persistence.

### Why SQLite and PostgreSQL support?

SQLite provides simple development and demonstration setup. PostgreSQL can be selected through the database environment configuration for larger production deployments.

### How are duplicate allocations prevented?

The system checks bed status, active student allocations, and active application allocations before creating a new allocation.

### How are payments confirmed?

An administrator confirms a pending payment only according to the configured accommodation required amount and cumulative confirmed payments linked to the allocation.

### How are reports protected?

Report routes validate roles and return management information without exposing passwords, reset tokens, verification tokens, or unrelated personal history.

### What happens during check-out?

The allocation becomes checked out, the related application becomes completed, and the bed returns to available status.
