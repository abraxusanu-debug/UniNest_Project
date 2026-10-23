# UniNest — University Hostel Management System

A centralized, web-based hostel management platform (student applications → verification →
allocation → payments → confirmation → check-in → maintenance → reports).

Built for the proposal *"Design and Development of a University Hostel Management System"*
by Victor Ndirangu (25/03338). See:

- `proposal/` — original 10-slide deck from the phone's Download folder (+ untouched copy)
- `deliverables/UniNest_10_Slide_Project_Proposal_CORRECTED.pptx` — deck with the budget total corrected (KSh 4,900) and a starting APA reference list on slide 10
- `deliverables/UniNest_Proposal_Revised.md` — revised written proposal
- `deliverables/UniNest_SRS.md` — requirements specification
- `deliverables/User_Manual.md` — user guide for students, admins, management
- `docs/ARCHITECTURE.md` — component and data-flow overview

## Quick start

```bash
cd backend
.venv/bin/python -m app.seed      # seed demo data (first run only)
.venv/bin/python run.py           # serve on http://127.0.0.1:5001
```

| Interface | URL |
|---|---|
| Web UI (server-rendered, zero JS deps) | http://127.0.0.1:5001 |
| REST API base | http://127.0.0.1:5001/api |
| Health check | http://127.0.0.1:5001/api/health |

Demo accounts (after seeding):

- **Admin** — `admin@uninest.ac.ke` / `Admin@123`
- **Management** — `management@uninest.ac.ke` / `Manage@123`
- **Students** — `miriam.otieno@student.ac.ke` etc. / `Student@123`

## Layout

```
backend/
  app/
    models/         SQLAlchemy models (users, students, hostels, rooms, beds,
                    applications, allocations, payments, maintenance, notifications)
    services/       business logic shared by API + web views
    routes/         JWT REST API under /api and the session-cookie web UI
    seed.py         demo data seeder
  templates/        Jinja2 pages (landing, auth, student, admin, reports)
  static/css/       hand-rolled design system — white theme, subtle shadows
  tests/            pytest suite (API + web journey)
  config.py  run.py backend/uninest.db
```

## Testing

```bash
cd backend
.venv/bin/python -m pytest tests -q          # 10 tests (API + web)
```

## Stack

Python 3.12+, Flask 3, Flask-SQLAlchemy, Flask-Migrate, Flask-JWT-Extended, Flask-CORS,
SQLite (default) / PostgreSQL-ready. No Node/npm — the frontend is fully server-rendered.
