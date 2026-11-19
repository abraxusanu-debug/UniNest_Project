---
title: 'Finalize UniNest release audit and GitHub update'
type: 'refactor'
created: '2026-11-19'
status: 'in-progress'
baseline_commit: 'f114a75'
context:
  - 'deliverables/UniNest_SRS.md'
  - 'deliverables/UniNest_Final_Submission_Plan.md'
  - 'README.md'
  - 'docs/ARCHITECTURE.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

The UniNest project has working code and deliverables, but prior corrections must be proven complete before release. This work audits implementation, requirements, reports, and presentation outputs, fixes only verified defects, removes generated or redundant artifacts, validates the application, and publishes a clean final GitHub state.

## Boundaries & Constraints

**Always:** Preserve existing student, admin, management, and maintenance workflows; keep role checks and service-layer lifecycle rules; use decimal payment values; keep database history; use the approved eight-character password policy; add tests for fixes; and leave a reproducible setup in the README.

**Ask First:** None. GitHub push is explicitly requested and the existing origin is authorized in the repository context.

**Never:** Do not invent interview evidence or respondent counts; do not claim a full payment gateway integration when office confirmation is the fallback; do not include secrets, passwords, reset tokens, verification tokens, or personal data in reports; do not rewrite unrelated features.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|-------------------------------|----------------|
| Payment sufficiency | Office-required amount exists and a pending payment is confirmed | Accommodation confirmation occurs only if cumulative or single payment meets the configured rule | Partial payment remains reconciliable and never confirms accommodation |
| Rejection timestamp | Admin rejects a pending payment | `failed` status and processing office/timestamp are retained | No allocation accommodation flags are changed |
| Registration edit | Verified student changes registration number | Number remains unique and verification status resets | Duplicate number is rejected |
| Withdrawal | Student withdraws pending/under-review application | Status becomes `withdrawn` and reapplication is allowed | Another status or owner is rejected |
| History-safe deletion | Hostel/room has occupied or historical allocation/application records | Deletion is blocked | Available unreferenced records may be deleted |
| Report export | Staff requests occupancy or allocation CSV | CSV is valid and excludes prohibited management fields | Student/API unauthorized requests return 403 |
| Release cleanup | Cache, database, duplicate uploads, or duplicate decks exist | Generated artifacts and source duplicates are removed or ignored | Required source deliverables remain tracked |

</frozen-after-approval>

## Code Map

- `backend/app/models/` -- entities and database constraints.
- `backend/app/services/` -- lifecycle, payment, account, and report rules.
- `backend/app/routes/` -- API and web validation/role enforcement.
- `backend/tests/` -- pytest coverage for API and web journeys.
- `deliverables/` -- SRS, proposal, final plan, user manual, and corrected slide deck.
- `docs/ARCHITECTURE.md` -- system and deployment facts.
- `README.md` and `backend/README.md` -- setup, test, and demo instructions.

## Tasks & Acceptance

**Execution:**
- [ ] `deliverables/UniNest_SRS.md`, `deliverables/UniNest_Final_Submission_Plan.md`, proposal, README, and architecture docs -- remove contradictions, stale counts, placeholders, and unsupported claims; add traceable final evidence and test references.
- [ ] `backend/app/models/payment.py`, `backend/app/models/mpesa_settings.py`, `backend/app/services/payment_service.py`, `backend/app/routes/web.py` -- implement an explicit office sufficiency rule and confirm/reject audit timestamps consistently.
- [ ] `backend/app/services/student_service.py`, `backend/app/services/application_service.py`, `backend/app/services/allocation_service.py`, `backend/app/services/hostel_service.py` -- verify uniqueness, verification reset, withdrawal/reapplication, cancellation/check-out, and history-safe deletion.
- [ ] `backend/tests/test_api.py`, `backend/tests/test_web.py`, `backend/tests/conftest.py` -- add focused regression coverage and retain full journey coverage.
- [ ] `deliverables/UniNest_10_Slide_Project_Proposal_CORRECTED.pptx` -- verify and correct the 10-slide presentation, references, budget, lifecycle, implementation, and demo readiness.
- [ ] `.gitignore`, repository inventory, generated cache/database/uploads -- remove unnecessary artifacts and prevent future cache, environment, database, and upload churn.
- [ ] GitHub -- run tests and clean status, commit all intended source/deliverable changes, and push the `main` branch to origin.

**Acceptance Criteria:**
- Given a partial or insufficient payment, when office confirmation is requested, then allocation flags remain unconfirmed and the payment stays reconciliable.
- Given a payment rejection or confirmation, when it is processed, then `confirmed_at` records the processing timestamp and confirmer/office identity remains available.
- Given the full pytest suite, when it is run, then all API and web journeys pass.
- Given staff report exports, when requested, then occupancy and allocation CSV data are complete and role guards deny unauthorized users.
- Given the slide deck, when inspected, then every slide has accurate content, the budget is consistent, and the deck is not redundant or corrupted.
- Given the GitHub working tree, when release work is complete, then only source, documentation, and intentional deliverables remain and `main` is pushed successfully.

## Spec Change Log

## Verification

**Commands:**
- `backend/.venv/bin/python -m pytest backend/tests -q` -- expected: complete suite passes.
- `git diff --check` -- expected: no whitespace errors.
- `git status --short --branch` -- expected: only intended changes after cleanup.
- `git push origin main` -- expected: origin/main updated successfully.

**Manual checks:**
- Open the corrected slide deck and confirm 10 slides, readable text, consistent budget, complete references, and a demo-ready sequence.
- Review SRS version, fact-finding status, lifecycle models, traceability, test matrix, and glossary for unresolved contradictions.
