# UniNest — Architecture

## Components

```
                       ┌────────────────────────────────────────────┐
   Browser ──HTTP────▶│ Flask app (backend/run.py, port 5001)       │
                       │                                            │
                       │  /            web.py (Jinja pages, session)│
                       │  /api/**      REST (JWT, role-protected)    │
                       │  /static/**   uni.css design system         │
                       │                                            │
                       │  Service layer (app/services/*)             │
                       │  ── student / hostel / application /        │
                       │     allocation / payment / maintenance /    │
                       │     report services                         │
                       │                                            │
                       │  SQLAlchemy ORM → SQLite (backend/uninest.db)│
                       └────────────────────────────────────────────┘
```

## Layers

1. **Routes** — two thin interfaces over the same services:
   - `routes/web.py` — server-rendered HTML (Jinja), session cookie auth, form POST + flash + redirect-after-post, role-gated views;
   - `routes/*.py` (REST) — JSON API with JWT Bearer tokens, same business rules.
2. **Services** (`app/services/*`) — all business rules and validation as plain functions raising
   typed `ServiceError` subclasses (`NotFound` 404, `Conflict` 409, `Forbidden` 403). Any pooled
   error handler turns them into JSON (`/api/*`) or flashed redirect (web).
3. **Models** — SQLAlchemy declarative models; computed properties (`beds_available`,
   `occupancy_rate`) keep UI/queries consistent.
4. **Persistence** — SQLite file in development; switch `UNINEST_DB_URI` to PostgreSQL in production.
   Migrations supported via Flask-Migrate.

## Business flow (core)

```
Student self-registers ──▶ Admin verifies ──▶ Student applies (pending)
        ──▶ Admin approves ──▶ Admin allocates free bed (allocation = "allocated")
        ──▶ Student records payment (pending) ──▶ Admin confirms
        ──▶ allocation.paid + accommodation_confirmed
        ──▶ Admin check-in ──▶ ... residence period ... ──▶ check-out (bed freed)

Two invariants enforce integrity:
  * one bed == at most one active allocation (bed.status drives availability)
  * one active application per student (pending/under_review/approved/allocated)
```

## Notifications

Every state change affecting a student (verification, application decision, allocation,
payment confirm/fail, maintenance progress) inserts a `notifications` row for the student,
surfaced in the web UI with an unread badge.

## Error contract

| HTTP | Raised as | JSON error field |
|---|---|---|
| 400 | `ServiceError` | `bad_request` |
| 401 | flask-jwt-extended | `unauthorized` |
| 403 | `Forbidden` / role guard | `forbidden` |
| 404 | `NotFound` | `not_found` |
| 409 | `Conflict` | `conflict` |
