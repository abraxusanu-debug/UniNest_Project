# UniNest — Revised Project Proposal

**Design and Development of a University Hostel Management System**

Proposed by: Victor Ndirangu · Registration No.: 25/03338
Supervisor: Geoffrey Rumbe
Revised edition — 2026

---

## 1. Project Overview

University students need suitable accommodation that supports both academic and social life. Hostel
administration currently coordinates students, applications, rooms, beds, payments and records using
manual forms, spreadsheets and physical registers, which are slow, error-prone and hard to audit.

**UniNest** is a centralized, web-based University Hostel Management System (UHMS). Students register
and apply online, while administrators manage records, allocations, payments and reports. Three
personas are served:

| Persona | Role in the system |
|---|---|
| Student | Register · Verify · Apply · Track status · Pay · Submit maintenance |
| Administrator | Verify students · Manage hostels/rooms/beds · Review & allocate · Confirm payments · Resolve maintenance · Reports |
| Management | Monitor occupancy · Review payment & vacancy reports (read-only) |

## 2. Problem Statement

1. Manual forms, spreadsheets and physical records make hostel management slow and error-prone.
2. Student information arrives through different channels (forms, WhatsApp, notice boards) during application and enrolment.
3. Administrators struggle to confirm current room and bed availability without physical checks.
4. Records become duplicated, outdated or difficult to retrieve.
5. Manual allocation, payment tracking and report preparation consume significant staff time.

## 3. Proposed Solution

A centralized web-based UHMS with the following modules:

1. **Student module** — self-service account, profile, hostel application with preferences, status tracking.
2. **Allocation module** — live room/bed availability and allocation of beds (Registration → Verification → Application → Review → Allocation → Payment → Confirmation → Check-in → Check-out).
3. **Payments & records** — payment records linked to students and their allocations; office confirmation marks accommodation as paid and confirmed.
4. **Admin module** — student verification, hostel/room/bed management, application review, allocation, payment confirmation.
5. **Maintenance module** — residents submit and track maintenance requests; office progresses them to resolution with notification feedback.
6. **Reporting** — occupancy, allocation, payment and vacancy reports (plus CSV export).

## 4. Objectives

**General objective.** Design and develop UniNest to improve student enrolment, hostel applications,
room allocation, payment records and hostel administration.

**Specific objectives.**

1. Investigate existing hostel enrolment and accommodation procedures.
2. Design a centralized database for students, hostels, rooms, beds, applications, payments and maintenance.
3. Develop student enrolment, hostel/room management and accommodation allocation modules.
4. Implement payment-record management and occupancy, allocation, payment and vacancy reports.
5. Evaluate the system against the identified requirements.

## 5. Significance of the Study

- **Students** — convenient registration, applications, status checks and accommodation information.
- **Hostel administrators** — centralized management of students, rooms, beds, applications, payments and records.
- **University management** — reports on occupancy, available accommodation, allocations and payments.
- **Hostel staff** — accommodation information plus check-in, check-out and maintenance support.
- **Future researchers** — a documented foundation for accommodation information-system research.

## 6. Literature Review (short version)

Traditional accommodation processes run on paper forms, notice boards and spreadsheets. Information
systems centralize organizational data in databases for authorized users (Laudon & Laudon, 2020).
Enrolment verification confirms students' eligibility before accommodation is assigned; computerized
allocation maintains live records of occupied and free beds. Digital payment records link money to
students and accommodation. Role-based access control keeps each user to authorized functions.
Research gap: no single coordinated system currently integrates enrolment, allocation, payment,
maintenance and reporting for the university (Kendall & Kendall, 2019; Chen, 1976).

## 7. Methodology

1. **Interviews** — hostel administrators and university personnel.
2. **Questionnaires** — students' accommodation experiences.
3. **Observation & document review** — application, allocation and payment processes.
4. **Agile development** — build in iterations, test, gather feedback, refine (Beck et al., 2001; Schwaber & Sutherland, 2020).

Development sequence: Requirements → System/database design → Modules → Testing → User evaluation → Deployment & documentation.

## 8. Intended Outcomes

1. A working UniNest web system (student, admin and management interfaces).
2. A centralized database of accommodation operations.
3. Automation of application review, bed allocation, payment confirmation and maintenance workflows.
4. Reporting including CSV exports for the university.
5. Documentation: SRS, user manual and revised proposal.

## 9. Budget (corrected)

| Item | Amount (KSh) |
|---|---|
| Internet / Data | 3,000 |
| Printing / Documentation | 200 |
| Transport / Research | 200 |
| Testing / Miscellaneous | 1,500 |
| Computer, hosting, domain, software | 0 (existing/free) |
| **Total** | **4,900** |

> **Correction note.** The draft proposal stated KSh 13,000 while its listed line items summed to
> KSh 4,900. The corrected total is **KSh 4,900**, matching the line items above. If additional
> items are required (e.g. domain or hosting), the schedule should be amended explicitly rather than
> increasing the total without itemization.

## 10. Schedule (22 weeks)

| Phase | Duration |
|---|---|
| Requirements & literature review | 4 weeks |
| Analysis and database / UI design | 4 weeks |
| Core modules development | 7 weeks |
| Reports, notifications & testing | 3 weeks |
| Evaluation, documentation & presentation | 4 weeks |

## 11. References

Laudon, K. C., & Laudon, J. P. (2020). *Management information systems: Managing the digital firm*
(16th ed.). Pearson.

Kendall, K. E., & Kendall, J. E. (2019). *Systems analysis and design* (10th ed.). Pearson.

Chen, P. P.-S. (1976). The entity-relationship model—toward a unified view of data. *ACM Transactions
on Database Systems, 1*(1), 9–36. https://doi.org/10.1145/320434.320440

Beck, K., Beedle, M., van Bennekum, A., Cockburn, A., Cunningham, W., Fowler, M., … Thomas, D. (2001).
*Manifesto for Agile software development*. https://agilemanifesto.org/

Sommerville, I. (2016). *Software engineering* (10th ed.). Pearson.

Schwaber, K., & Sutherland, J. (2020). *The Scrum Guide*. Scrum.org. https://scrumguides.org/

W3C. (2018). *Web Content Accessibility Guidelines (WCAG) 2.1*. https://www.w3.org/TR/WCAG21/

> **Note for the author.** Before submission, replace or extend these with the sources actually
> consulted during the literature review, keeping APA 7 formatting. Where no local sources were used,
> add university library reports/web sources reviewed. In-text citations above match this list.
