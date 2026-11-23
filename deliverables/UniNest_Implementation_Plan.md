# UniNest — Implementation Plan

**Version:** 1.0
**Status:** Work in Progress
**Date:** 23 November 2026
**Student:** Victor Ndirangu (25/03338)

## 1. Purpose

This plan describes the remaining work, implementation sequence, ownership, deliverables, quality gates, and release activities for UniNest.

## 2. Implementation strategy

UniNest uses an incremental implementation model: requirements and data integrity first, service-level lifecycle rules next, thin routes after, then automated tests and documentation.

## 3. Work packages

### WP1 — Requirement and data correction
- Finalize SRS fields and lifecycle rules.
- Keep registration number and email uniqueness.
- Preserve eight-character passwords.
- Use decimal payment values and explicit sufficiency policy.
- Protect records with application or allocation history.

**Exit:** SRS, code, and tests use identical rules.

### WP2 — Account and security workflows
- Harden registration and login validation.
- Implement verification and role checks.
- Apply login throttling and account deactivation.
- Add CSRF to web forms and configure secure session options.
- Audit password reset and verification workflows.

**Exit:** Automated security tests pass.

### WP3 — Hostel and application workflows
- Maintain hostel, room, and bed inventory.
- Implement application submission, review, withdrawal, and reapplication.
- Enforce allocation, check-in, check-out, cancellation, and bed availability.
- Prevent concurrent allocations and incorrect state transitions.

**Exit:** Lifecycle and API/web journey tests pass.

### WP4 — Payment and maintenance workflows
- Implement pending/confirmed/failed payment states.
- Confirm or reject based on configured office sufficiency.
- Retain processing timestamps and office identity.
- Process maintenance submitted/in-progress/resolved states.
- Prevent resolved maintenance from reopening.

**Exit:** Payment and maintenance regression tests pass.

### WP5 — Notifications and reports
- Create in-app notifications for key transitions.
- Send privacy-safe email notifications.
- Restrict management fields.
- Export occupancy and allocation reports as CSV.

**Exit:** Role guards and privacy checks pass.

### WP6 — Test automation and UAT
- Extend pytest coverage for fixed lifecycle and security scenarios.
- Run API and web suites.
- Prepare browser and keyboard-only UAT checklist.
- Log defects and verify corrections.

**Exit:** 17 existing tests plus approved new tests pass; no open critical/high defects.

### WP7 — Documentation and release
- Finalize SRS, SDS, test plan, implementation plan, final report, and user manual.
- Update README and architecture documentation.
- Generate PDF deliverables where tooling permits.
- Review repository and remove generated caches/databases from source control.

**Exit:** Clean Git state and reviewed submission files.

## 4. Suggested schedule

| Phase | Timing | Output |
|---|---|---|
| Requirements freeze | 24 Nov 2026 | Reviewed SRS and traceability |
| Core implementation audit | 25–26 Nov 2026 | Service/lifecycle corrections |
| Security hardening | 27 Nov 2026 | CSRF, lockout, session review |
| Test expansion | 28–30 Nov 2026 | Focused pytest cases |
| UAT and defect closure | 1–3 Dec 2026 | UAT evidence and defect closure |
| Report and manual finalization | 4–6 Dec 2026 | Final deliverables |
| Submission rehearsal | 7–8 Dec 2026 | Demo and PDF readiness |

These dates are a work-plan proposal and shall be revised against the actual submission deadline.

## 5. Technical tasks and modules

| Area | Primary files |
|---|---|
| Models | `backend/app/models/*.py` |
| Services | `backend/app/services/*.py` |
| REST | `backend/app/routes/*.py` |
| Web UI | `backend/app/routes/web.py`, `backend/templates/**` |
| Tests | `backend/tests/test_api.py`, `test_web.py`, `conftest.py` |
| Documentation | `deliverables/**`, `README.md`, `docs/ARCHITECTURE.md` |

## 6. Quality gates

### Gate 1 — Requirements
- Requirement IDs are stable.
- Contradictory states and fields are removed.

### Gate 2 — Implementation
- Routes delegate lifecycle rules to services.
- Database transitions preserve referential integrity.

### Gate 3 — Security
- Password, role, JWT, session, CSRF, and lockout checks pass.

### Gate 4 — Testing
- Full pytest suite passes.
- CSV and browser journeys pass manual checks.

### Gate 5 — Release
- Deliverables are complete and internally consistent.
- Git diff has no whitespace or accidental secret changes.

## 7. Test commands

```bash
cd backend
/data/data/com.termux/files/usr/bin/python -m pytest tests -q
```

Repository checks:

```bash
cd /data/data/com.termux/files/home/Desktop/UniNest_Project
git diff --check
git status --short --branch
```

## 8. Risks and responses

| Risk | Probability | Impact | Response |
|---|---|---|---|
| Live email unavailable | Medium | Medium | Continue with logged/in-app notifications and a mocked test adapter |
| Missing external payment gateway | Medium | Medium | Keep office confirmation and explicitly exclude settlement |
| SQLite-to-PostgreSQL incompatibility | Medium | Medium | Keep SQL portable and run migration smoke tests |
| Deadline pressure | Medium | High | Freeze scope and prioritize MUST requirements |
| Data loss during migration | Low | High | Back up database and test migrations on copies |

## 9. Completion criteria

- Core workflows demonstrated end-to-end.
- SRS, SDS, test plan, implementation plan, report, and manual are complete.
- Automated suite passes.
- Demonstration environment is available offline.
- Submission repository contains only source and intentional deliverables.
