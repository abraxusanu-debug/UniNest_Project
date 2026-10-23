# UniNest — System Requirements Specification (SRS)

Version 1.0 · 2026 · Victor Ndirangu (25/03338)

## 1. Purpose and scope

UniNest is a web-based University Hostel Management System (UHMS) that centralizes student
enrolment/verification, hostel applications, room/bed allocation, payment records, maintenance
requests and reporting in place of manual forms and spreadsheets.

In-scope: student and staff workflows described in §3; reports; CSV export.
Out-of-scope: online payment gateway integration (records are confirmed manually by the hostel
office), SMS notifications, university ERP integration.

## 2. System overview

| Layer | Technology |
|---|---|
| Web frontend | Flask/Jinja2 server-rendered templates, custom CSS design system (no third-party JS) |
| REST API | Flask 3, JWT (Bearer) authentication, role-based permissions |
| Application layer | Service layer (`app/services/*`) shared by API and web views |
| Persistence | SQLAlchemy ORM; SQLite (dev) / PostgreSQL (production-ready) |
| Data model | see §4 |

## 3. Functional requirements

### 3.1 Users and roles

- FR-1: The system SHALL register students (self-service) with account status `unverified`.
- FR-2: Admins SHALL verify/unverify student records. Unverified students cannot apply.
- FR-3: Three roles exist: `student`, `admin`, `management` — enforced on both API and web routes.

### 3.2 Hostels

- FR-4: Admins SHALL create hostels (name, gender policy male/female/mixed, location, description).
- FR-5: Admins SHALL create rooms per hostel (number, floor, type shared/single, optional bed count auto-generated).
- FR-6: Admins SHALL add/remove beds and mark beds `available`/`maintenance` (occupied beds are locked to allocation lifecycle).
- FR-7: The system SHALL NOT allow deleting hostels/rooms with occupied beds.
- FR-8: Availability (free/occupied/maintenance counts) SHALL be visible to all roles.

### 3.2 Applications and allocation

- FR-9: Verified students SHALL submit one active application at a time (status: pending → under_review → approved/rejected → allocated).
- FR-10: Admins SHALL review applications (approve/reject/under review) with notes.
- FR-11: Admins SHALL allocate an approved application to one of the free beds; the bed becomes `occupied`.
- FR-12: Admins SHALL record check-in (allocated → checked_in) and check-out (checked_in → checked_out; frees the bed).
- FR-13: Admins SHALL cancel allocations; cancelling frees the bed and returns the application to `approved`.
- FR-14: Students SHALL receive a notification on every credential status change.

### 3.3 Payments

- FR-15: Students SHALL record payments (amount, method mpesa/bank/cash/card, allocation linkage, semester).
- FR-16: Admins SHALL confirm or reject pending payments.
- FR-17: Confirming a payment on an active allocation SHALL mark the allocation `paid` and `accommodation_confirmed`.

### 3.4 Maintenance

- FR-18: Students SHALL submit maintenance requests (title, description, priority low/medium/high) linked to their allocated room by default.
- FR-19: Admins SHALL progress requests: submitted → in_progress → resolved (with resolution note). Resolved requests cannot be reopened.

### 3.5 Reporting

- FR-20: Admin/management SHALL view: occupancy report per hostel, vacancies per room, payments by method/status/semester, allocation registers.
- FR-21: Admin/management SHALL download occupancy and allocations as CSV.
- FR-22: All key actions SHALL emit notifications to affected students.

## 4. Data model

- **users** — email(uniq), password_hash, full_name, role, is_active
- **students** — user_id(uniq), registration_no, program, year_of_study, phone, gender, verification_status, verified_at
- **hostels** — name(uniq), gender, location, description
- **rooms** — hostel_id → hostels, number, floor, room_type; UNIQUE(hostel_id, number)
- **beds** — room_id → rooms, bed_number, status available|occupied|maintenance
- **applications** — student_id, preferred_hostel_id, room_preference, notes, status, review_notes, reviewed_by, reviewed_at
- **allocations** — student_id, bed_id, application_id, status allocated|checked_in|checked_out|cancelled, paid, accommodation_confirmed, allocated_by, check_in_date, check_out_date
- **payments** — reference(uniq, `UNI-…`), student_id, allocation_id, amount, method, semester, status pending|confirmed|failed, confirmed_by, confirmed_at
- **maintenance_requests** — allocation_id, student_id, title, description, priority, status, resolution_note, resolved_by, resolved_at
- **notifications** — user_id, type, title, message, is_read

## 5. Non-functional requirements

- NFR-1 Security: bcrypt-class password hashing (werkzeug), JWT for API (12 h expiry), server-side session cookies (HttpOnly, SameSite=Lax) for web, role checks on every protected route.
- NFR-2 Usability: minimal, mobile-friendly UI; white theme with subtle shadows; confirmation dialogs for destructive actions.
- NFR-3 Portability: zero build tooling — runs with Python 3.12+ and pip only; SQLite default database.
- NFR-4 Performance: indexed lookups on foreign keys, statuses, email and registration numbers; sub-second response for single-instanced campus use.
- NFR-5 Maintainability: service layer isolates business rules so API and web UI stay thin.
- NFR-6 Accessibility: keyboard-focusable controls, semantic HTML5, WCAG-minded contrast levels.

## 6. API summary (JWT)

| Method & path | Role | Purpose |
|---|---|---|
| POST /api/auth/register, POST /api/auth/login | public | register/login |
| GET /api/auth/me | any | current user |
| GET/PUT /api/students/me | student | profile |
| GET /api/students, POST /api/students/:id/verify | admin | verification |
| GET/POST/PUT/DELETE /api/hostels… | mixed | hostels/rooms/beds |
| POST /api/applications, /:id/review | student / admin | apply & review |
| POST /api/allocations, /:id/check-in, /:id/check-out | admin | allocation lifecycle |
| POST /api/payments, /:id/confirm, /:id/fail | student / admin | payments |
| POST /api/maintenance, /:id/status | student / admin | maintenance |
| GET /api/notifications (+ /read-all) | any | notifications |
| GET /api/reports/* (+ .csv) | admin, management | reports |

## 7. Verification and validation

- Backend unit/API tests: `pytest` (10 tests).
- End-to-end API journey script: 26 assertions covering the full business lifecycle and permission guards.
- Browser-style web journey test: 24 assertions (register → verify → apply → approve → allocate → pay → confirm → maintenance → reports), cookie session based.
