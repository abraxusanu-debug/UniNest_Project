# UniNest backend

Flask application: JWT REST API + session-based server-rendered web UI, sharing one service layer.

## Run

```bash
python3 -m venv .venv                  # once
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m app.seed           # demo data (safe: skips if db already populated)
.venv/bin/python run.py                # http://127.0.0.1:5001
```

Environment variables: `UNINEST_DB_URI` (default `sqlite:///<this dir>/uninest.db`),
`UNINEST_SECRET_KEY`, `UNINEST_JWT_KEY`.

## Structure

```
app/
  __init__.py     app factory + error handlers + blueprints
  extensions.py   db, migrate, jwt
  models/         User, Student, Hostel, Room, Bed, Application, Allocation,
                  Payment, MaintenanceRequest, Notification
  services/       business logic; errors.py defines ServiceError/NotFound/Conflict/Forbidden
  routes/         auth, students, hostels, applications, allocations, payments,
                  maintenance, notifications, reports (REST) + web.py (server-rendered UI)
  seed.py         demo seeder (2 hostels, 12 rooms, 48 beds, 4 students, live allocations)
templates/        index, auth/{login,register}, student/{dashboard,apply,availability,payments,
                  maintenance,notifications,profile}, admin/{dashboard,students,hostels,applications,
                  allocations,payments,maintenance}, management/dashboard, reports, 404, base
static/css/uni.css  design system (white theme, subtle shadows, badges, bar charts)
tests/            conftest.py, test_api.py, test_web.py  (API and web pytest suite)
config.py         Config (dev) / TestConfig (in-memory sqlite)
run.py            entrypoint (port 5001)
```

## Tests

```bash
.venv/bin/python -m pytest tests -q
```

Covers: register/login/me, verification gate, application lifecycle, allocation lifecycle,
payment confirmation side-effects, report permissions, and the full web journey (register →
verify → apply → approve → allocate → pay → confirm → maintenance → reports via HTML forms).
