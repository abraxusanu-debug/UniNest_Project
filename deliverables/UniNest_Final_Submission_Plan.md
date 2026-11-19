# UniNest Final Submission Plan

## 1. Objective
Complete the SRS v2.0 corrections, align the implementation with the final requirements, and prepare the project report, slides, and demonstration for the final presentation.

## 2. Sources Used
- SRS writing guideline: purpose, scope, users, existing/proposed system, numbered functional and non-functional requirements, models, data requirements, appendices, and definitions.
- Final DTA presentation notice: final presentations are on 20 November 2026. Students need a stable connection, microphone, camera, and their project report, slides, and demonstration ready.
- SRS v2.0 review feedback: correctness, integrity, lifecycle, security, traceability, and presentation issues.

## 3. Must-Fix SRS and Implementation Work

### A. Data and account integrity
1. Align registration fields across FR-01, Section 8.1, and Appendix C.1. Decide and document whether registration number, programme, year, phone, and gender are required or optional.
2. Make `registration_no` unique. Prevent editing after verification or reset verification automatically when it changes.
   - Update `backend/app/models/student.py` and `backend/app/services/student_service.py`.
3. Replace the own-personal-data example and all sample-date placeholders with clearly distinct dummy values.
4. Raise password minimum from six to eight characters in requirements and code.
   - Update registration, maintenance-account creation, reset-password code, validation, and tests.
5. Remove or close all defects currently described as deviations. Fix management check-in/check-out, password policy, and pagination conflicts.
6. Include actual Mermaid source for use-case, context, ERD, or state diagrams, or remove the claim that Mermaid sources are included.

### B. Fact-finding evidence
7. Add an evidence summary for interviews and questionnaire: interviewees, respondent count, dates, key findings, and traceability to P1–P9 and relevant requirements.
8. Map each finding to one or more functional requirements and test cases.

### C. Account and application lifecycle
9. Document administrator and management account creation, password change/reset, account deactivation, and role recovery.
10. Add student withdrawal for pending or under-review applications.
11. Define closed application and allocation transitions:
   - check-out closes allocation and application;
    - cancellation returns allocation and application to `approved` where appropriate;
    - withdraw changes an application to `withdrawn`;
    - reapplication is permitted only after the previous application is closed.
12. Add `maintenance → available` and `allocated → approved` cancellation transitions to state tables.

### D. Payment, deletion, and data rules
13. Define payment sufficiency for allocation confirmation. The office must have an explicit required amount or policy, not “any confirmed amount.”
14. Define the handling of confirmed payments without an allocation and reconcile the allocation/payment lifecycle.
15. Change money storage from Float to a decimal/decimal-precision type. Separate confirmed/rejected timestamps or document the intended semantics for `confirmed_at`.
16. Replace deleted hostels/rooms with soft-deletion or block deletion whenever application or allocation history exists.

### E. Security and privacy
17. Add CSRF protection to web forms and login throttling or lockout.
18. Specify the exact student fields visible to management and keep only necessary fields accessible.
19. Add a SHOULD rule warning before a mismatched gender allocation is attempted.
20. Remove SameSite=Lax as the sole web security claim; retain HttpOnly and document CSRF controls.

## 4. Requirement Quality
- Make NFR-P4, NFR-U5, and NFR-AC2 measurable or reword them.
- Rebalance MoSCoW priorities: at least several SHOULD/COULD requirements, while keeping critical security and lifecycle rules as MUST.
- Add P1–P9 → FR traceability.
- Extend the requirements-to-test matrix, especially FR-48–FR-58 and all lifecycle/payment/security requirements.
- Add or remove references consistently. Cite the current standards, use ISO/IEC/IEEE 29148:2018 instead of claiming IEEE 830-1998 is current, and remove unused sources.
- Correct version history to use full dates, separate software package versions, and remove WORM from the glossary.
- Fix wrapped table headers and any OCR-style word breaks.

## 5. Implementation and Test Sequence

### Phase 1 — Requirements and model corrections
- Update `deliverables/UniNest_SRS.md` first, including fields, lifecycle, NFRs, traceability, diagrams, evidence, and priorities.
- Update `backend/app/models/student.py`, `backend/app/models/payment.py`, hostel/application models, and relevant migrations.

### Phase 2 — Service and route corrections
- Update `backend/app/services/student_service.py`, application, allocation, payment, hostel, and authentication services.
- Add unique constraints, soft-delete, withdrawal, payment sufficiency, and logout/session behaviors as specified.
- Update web and API validation so routes enforce the same rules.

### Phase 3 — Security
- Configure CSRF for web forms.
- Implement login throttling or lockout using a bounded, testable policy.
- Use the eight-character password policy consistently everywhere.

### Phase 4 — Verification
- Add focused tests for uniqueness, locked/changed registration numbers, withdrawal, checkout/reapplication, cancellation, payment sufficiency, decimal values, soft deletion, CSRF, lockout, and gender warnings.
- Run `pytest` and browser/API journeys, then update test counts and the requirements-to-test matrix.
- Check the report for contradictions, unresolved deviations, broken links, table wrapping, and document version consistency.

## 6. Presentation Readiness
- Finalize the report and SRS PDF from the reviewed source document.
- Prepare a 10–15 minute demo flow: login → verify student → apply → review → allocate/check-in/check-out → payment → maintenance → reports.
- Confirm the meeting link and panel schedule are received before the presentation.
- Join with the official name and registration number at least 10 minutes early, test camera/microphone/network, and keep the demonstration prepared offline where possible.

## 7. Acceptance Checklist
- [ ] Every feedback point has a requirement or closed-defect disposition.
- [ ] SRS and code use the same registration, password, lifecycle, payment, and deletion rules.
- [ ] No unresolved DEV entry or contradictory NFR remains.
- [ ] Every MUST requirement has an implementation and test reference.
- [ ] P1–P9 and FR-48–FR-58 are traceable.
- [ ] Mermaid or equivalent diagrams and fact-finding evidence are complete.
- [ ] Final report, slides, demo, and network setup are tested before 20 November 2026.
