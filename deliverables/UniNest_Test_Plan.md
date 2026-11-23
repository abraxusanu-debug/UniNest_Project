# UniNest — Test Plan

**Version:** 1.0
**Status:** Work in Progress
**Date:** 23 November 2026
**Project:** Diploma in Information Technology
**Prepared by:** Victor Ndirangu (25/03338)

## 1. Test objectives

Verify that UniNest implements the requirements in `UniNest_SRS.md`, preserves role separation, maintains lifecycle integrity, and remains usable for all core workflows.

## 2. Scope

### In scope
- Registration, authentication, password policy, verification, and role authorization.
- Hostel, room, bed, application, allocation, payment, maintenance, and report workflows.
- REST API and server-rendered web UI journeys.
- Data integrity, privacy, reporting, responsive presentation, and error handling.

### Out of scope
- Live M-Pesa settlement or direct Daraja disbursement.
- University ERP integration.
- High-volume distributed load testing and external penetration testing.

## 3. Test levels

| Level | Purpose | Location |
|---|---|---|
| Unit/service | Validate isolated business and lifecycle rules | `backend/tests/` and future focused test modules |
| API integration | Verify endpoint behavior, authentication, JSON contracts, and roles | `test_api.py` |
| Web integration | Verify HTML workflows and form/redirect behavior | `test_web.py` |
| End-to-end journey | Exercise register → verify → apply → allocate → pay → confirm → maintenance | `test_web.py` |
| UAT | Observe representative student, office, management, and maintenance users | Scheduled before submission |

## 4. Test environment

- Python 3.12 or later
- Flask test application with in-memory SQLite
- pytest and Flask test client
- Chromium or current mobile/desktop browser for manual testing
- Configured demo accounts from `app.seed`

## 5. Entry and exit criteria

### Entry
- Application starts successfully.
- Test database is created and seeded without external services.
- SRS requirements have stable IDs.

### Exit
- All planned automated tests pass.
- No open critical or high-severity defect.
- Core UAT scenarios complete successfully.
- Test evidence and command output are retained in the final report.

## 6. Test data

Use synthetic names, emails, registration numbers, and payments. Do not use real student credentials or sensitive personal records. Demo records are reset in the test database for every fixture run.

## 7. Automated test inventory

| Suite | Tests | Current coverage |
|---|---:|---|
| API | 9 | Health, auth, verification, applications, allocations, payments, privacy policy, reports |
| Web | 8 | Login/logout, registration, hostel management, profile, uploads, M-Pesa settings, maintenance account, full journey |
| Total | 17 | 17 passed on 23 November 2026 |

## 8. Requirements-to-test matrix

| Requirement area | Representative automated test | Manual/needed test |
|---|---|---|
| FR-01–FR-12 Authentication | `test_register_login_me`, `test_password_and_notification_email_policy` | Login throttling, account deactivation, registration edit |
| FR-13–FR-20 Inventory | `test_admin_manage_hostel_through_web`, `test_student_full_web_journey` | Gender mismatch warning and history-safe deletion |
| FR-21–FR-31 Applications/allocations | `test_application_flow_requires_verification`, `test_allocation_bed_lifecycle` | Withdrawal, cancellation, reapplication |
| FR-32–FR-39 Payments | `test_payment_confirm_updates_allocation`, `test_partial_payment_does_not_confirm_accommodation`, `test_rejected_payment_has_processing_audit` | Confirmed payment without allocation and cumulative sufficiency |
| FR-40–FR-43 Maintenance | `test_student_full_web_journey`, `test_admin_can_setup_maintenance_worker_account` | Resolution cannot reopen |
| FR-44–FR-48 Notifications/privacy | `test_password_and_notification_email_policy` | Read-all and privacy-sensitive email review |
| FR-49–FR-51 Reports | `test_reports_and_guards` | CSV at 10,000 records and field minimization |
| NFR-S1–S7 Security | API role tests, password test | CSRF and 15-minute lockout verification |
| NFR-U1–U5 Usability | Manual viewport and keyboard checks | 360 px/768 px, keyboard-only pilot |
| NFR-R1–R4 Reliability | API/web transaction journeys | Failure injection and orphan record check |

## 9. Detailed test cases

### T01 Registration and login
- Enter valid and invalid credentials.
- Confirm duplicate email and short passwords are rejected.
- Confirm successful login creates a JWT or web session.

### T02 Verification gate
- Unverified student cannot apply.
- Admin verifies student.
- Verified student may submit an application.

### T03 Application lifecycle
- Submit pending application.
- Move to under review and approve/reject.
- Withdraw pending or under-review application.
- Reapply only after closure.

### T04 Allocation lifecycle
- Allocate an approved application to an available bed.
- Check in, check out, and cancel.
- Confirm bed and application state changes remain consistent.

### T05 Payment reconciliation
- Confirm a sufficient payment and confirm accommodation.
- Confirm a partial payment below the configured threshold and keep flags false.
- Reject a payment and verify processing timestamp and office identity.

### T06 Maintenance
- Create a submitted request.
- Start and resolve it.
- Confirm resolved requests cannot reopen.

### T07 Reports and exports
- Administrator and management can access summaries.
- Student is denied.
- CSV is complete, readable, and excludes protected fields.

### T08 Security and privacy
- Unauthorized route access is denied.
- CSRF-invalid web POST is rejected.
- Email body does not disclose sensitive values.
- Invalid or expired JWT is denied.

## 10. Defect severity

| Severity | Definition |
|---|---|
| Critical | Security breach, corrupted records, or core workflow unavailable |
| High | Major requirement or role workflow incorrect |
| Medium | Feature usable but with incorrect guidance or secondary defect |
| Low | Cosmetic or documentation-only defect |

## 11. Execution procedure

```bash
cd backend
/data/data/com.termux/files/usr/bin/python -m pytest tests -q
```

For browser/UAT checks, seed demo data and run `python run.py`, then follow the user manual's role workflows.

## 12. Risks

- External email delivery is not available in test environments.
- Browser and keyboard tests may vary across devices.
- SQLite behavior differs from PostgreSQL for some configuration and concurrency scenarios.
- Live M-Pesa testing is excluded; office-confirmed payment reconciliation is tested instead.

## 13. Deliverables

- Automated pytest evidence
- Browser screenshots or UAT checklist
- Defect log
- Final requirements traceability summary
