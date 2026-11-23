# UniNest — User Manual

**Version:** 2.0
**Status:** Final for demonstration
**Date:** 23 November 2026

A practical guide for students, hostel administrators, management users, and maintenance staff.

## 1. Starting the system

### 1.1 Prerequisites

- A modern desktop or mobile browser
- Python 3.12 or later
- Internet or local network access to the UniNest server

### 1.2 Start in development

```bash
cd backend
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m app.seed
.venv/bin/python run.py
```

Open **http://127.0.0.1:5001**. The landing page shows live availability.

### 1.3 Demo accounts

| Role | Email | Password |
|---|---|---|
| Administrator | admin@uninest.ac.ke | Admin@123 |
| Management | management@uninest.ac.ke | Manage@123 |
| Student | miriam.otieno@student.ac.ke | Student@123 |

Change demo passwords before using a public or production deployment.

## 2. Student guide

### 2.1 Create an account

1. Select **Create account**.
2. Enter full name, email, password, registration number, programme, year of study, phone number, and gender.
3. Use at least eight characters for the password.
4. Submit the registration form.
5. Check in-app notifications and email for account and login messages.

An account may be unverified until the hostel office confirms it. Unverified students cannot submit accommodation applications.

### 2.2 Submit an application

1. Open **Dashboard** and select **Apply now**.
2. Choose a preferred hostel and room type if these fields are offered.
3. Add a clear note about any relevant preference or requirement.
4. Submit the application.
5. Track `pending`, `under_review`, `approved`, or a closed state on the dashboard.

Only one active application is allowed at a time. A pending or under-review application may be withdrawn from the application view.

### 2.3 View and withdraw an application

Open **Applications** or the dashboard application card. The status and review notes show the latest office decision. If the application is pending or under review, select **Withdraw**. After withdrawal or rejection, the student may submit a new application when the prior record is closed.

### 2.4 Receive an allocation

After the office approves and allocates an application:

- A notification appears in the account.
- The allocation is visible on the student dashboard.
- The bed and room details show in the allocation view.
- Status begins as `allocated`, then becomes `checked_in` when the student is admitted.

### 2.5 Record a payment

1. Open **Payments**.
2. Select the allocation.
3. Enter amount, payment method, semester, and optional description.
4. Submit the payment.

The payment initially has `pending` status. A partial payment may remain reconciliable but does not confirm accommodation unless the configured office sufficiency rule is met. The office confirms or rejects the payment record.

UniNest is not a live settlement gateway. The office must verify genuine M-Pesa or other office-approved payment evidence.

### 2.6 Submit a maintenance request

1. Open **Maintenance**.
2. Enter the issue description and priority.
3. Submit the request.
4. Use the page to follow `submitted`, `in_progress`, and `resolved`.

Resolved requests cannot reopen. A resolution note identifies the work completed.

### 2.7 Update profile and notifications

The **Profile** page permits permitted personal and academic fields. Changing a verified registration number follows verification safety rules. Open **Notifications** to view application, allocation, payment, maintenance, and account messages. Notifications may be marked as read individually or all at once.

## 3. Administrator guide

### 3.1 Dashboard

The dashboard summarizes pending applications, unverified students, occupancy, pending payments, and maintenance queues. Use the quick links to open the relevant queue.

### 3.2 Manage students

- Search or open the student register.
- Verify a student after checking enrolment evidence.
- Unverify or deactivate an account when authorized.
- Confirm duplicate registration numbers are not created.

An unverified student cannot apply for accommodation.

### 3.3 Manage hostels and beds

1. Open **Hostels**.
2. Create or edit the hostel name, gender policy, location, description, image, and amenities.
3. Add rooms and configure bed counts.
4. Mark an unallocated bed as `maintenance` or return it to `available` when safe.
5. Delete only an empty hostel or room with no occupied bed or protected history.

Do not delete historical accommodation records; UniNest blocks deletion when history would be lost.

### 3.4 Review applications

- Open **Applications**.
- Move a pending application to `under_review`.
- Add review notes and approve or reject it.
- Reject or allow withdrawal to close an application and permit reapplication.

### 3.5 Allocate and manage accommodation

1. Open the **Approved** applications tab.
2. Select an available bed for the application.
3. Allocate the bed.
4. Record **Check in** when the student arrives.
5. Record **Check out** when the student leaves; this releases the bed.
6. Use **Cancel** only according to office policy to return an application to approved and free the bed.

### 3.6 Confirm payments

1. Open **Payments**.
2. Review pending records and external evidence.
3. Confirm or reject the payment.
4. If the cumulative confirmed amount meets the configured office-required amount, accommodation confirmation flags are set.
5. Insufficient payments remain confirmed payment records but do not confirm accommodation unless the full policy is satisfied.

### 3.7 Process maintenance

Open **Maintenance**, choose **Start** for a submitted request, and add a resolution note before selecting **Resolve**. Resolved items are closed.

### 3.8 Generate reports

Open **Reports** to view occupancy, free beds, payment totals, allocation records, and maintenance summaries. Download occupancy or allocation CSV files for spreadsheet use.

## 4. Management guide

Management users may view:

- The management dashboard
- Occupancy and availability
- Operational reports
- Allocation and accommodation summaries
- Confirmed payment totals

Management users cannot reset passwords, manage hostel inventory, approve applications, confirm payments, or modify accommodation records unless an administrator account performs those functions separately.

## 5. Maintenance staff guide

Maintenance staff may open the maintenance queue, review descriptions and priorities, move a request to `in_progress`, and resolve it with a clear note.

## 6. Status reference

| Object | Status sequence |
|---|---|
| Student | unverified → verified |
| Application | pending → under_review → approved / rejected / withdrawn / allocated / completed |
| Allocation | allocated → checked_in → checked_out or cancelled |
| Bed | available / occupied / maintenance |
| Payment | pending → confirmed / failed |
| Maintenance | submitted → in_progress → resolved |

## 7. Troubleshooting

| Symptom | Likely cause and action |
|---|---|
| Account is unverified | Contact the hostel office. The office must verify enrolment. |
| Cannot submit application | Another active application may exist, or verification is incomplete. |
| Bed dropdown is empty | No bed is available. Review occupancy and maintenance beds. |
| Payment remains unconfirmed | A partial payment has not met the office sufficiency rule. |
| Hostel or room cannot be deleted | It is occupied or retains application/allocation history. |
| Login is rejected after failures | Login lockout may be active. Wait for the configured 15-minute period. |
| Access is denied | The account role does not permit that operation. |
| CSV download is unavailable | Only administrator and management roles are permitted. |
| Maintenance cannot reopen | Resolved requests are closed by policy. |

## 8. API overview

API clients use `POST /api/auth/login` to obtain a JWT, then send `Authorization: Bearer <token>` to protected endpoints. Core resources are under `/api/students`, `/api/hostels`, `/api/applications`, `/api/allocations`, `/api/payments`, `/api/maintenance`, `/api/notifications`, and `/api/reports`.

Use the API only through authenticated clients. Do not place secrets or passwords in issue reports, screenshots, browser URLs, or source-controlled configuration.

## 9. Support checklist

Before requesting support, record:

- Screenshot of the affected page
- Account role, not the password
- Date and approximate time
- Action attempted
- Error message
- Browser and device type

Do not send passwords, reset links, verification tokens, payment phone numbers, or unrelated personal records.
