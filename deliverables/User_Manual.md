# UniNest — User Manual

A short guide for students, hostel administrators and university management users.

## 1. Starting the system

```bash
cd backend
.venv/bin/python -m app.seed   # one-time demo data (accounts + hostels + beds)
.venv/bin/python run.py        # serves http://127.0.0.1:5001
```

Open **http://127.0.0.1:5001** in a browser. The landing page shows live hostel availability.

Demo accounts (after seeding):

| Role | Email | Password |
|---|---|---|
| Administrator | admin@uninest.ac.ke | Admin@123 |
| Management | management@uninest.ac.ke | Manage@123 |
| Student | miriam.otieno@student.ac.ke | Student@123 |

## 2. For students

### 2.1 Register
1. Click **Create account** and fill in your name, registration number, programme, year, gender, phone, email and password.
2. You are logged in immediately, but your **account is unverified** — the hostel office checks your enrolment record.

### 2.2 Apply for accommodation
1. Once verified you will see a green `verified` pill on your profile.
2. Open **Dashboard → Apply now** (or Dashboard → apply card when no application exists).
3. Choose a preferred hostel (optional), room type and add notes.
4. Submit. Track the status on your dashboard: **pending → under review → approved**.

### 2.3 Get allocated and pay
1. When the office approves your application they allocate you a **bed**; you receive a notification.
2. Go to **Payments**, choose your allocation, enter the amount and method (e.g. M-Pesa), and submit.
3. The office confirms your payment; your dashboard then shows **paid · confirmed**.

### 2.4 Maintenance
1. Open **Maintenance**, describe the issue (e.g. "leaking tap"), set priority and submit.
2. Watch status: **submitted → in progress → resolved** (with the office's resolution note).

### 2.5 Profile & notifications
- **Profile** — update programme/year/phone at any time.
- **Notifications** — every change to your application, allocation, payment or maintenance requests appears here.

## 3. For administrators

- **Dashboard** — counters for pending applications, students awaiting verification, occupancy and pending payments, with quick links to each queue.
- **Students** — verify or unverify students. Unverified students cannot apply.
- **Hostels** — add hostels; add rooms (bed count auto-creates beds); add more beds to a room; mark beds under maintenance; delete empty hostels/rooms. Beds allocated to students are protected.
- **Applications** — review queued applications: *Review* (move to under review), *Approve*, *Reject*. On the **Approved** tab, pick a free bed from the dropdown and click **Allocate**.
- **Allocations** — record **check in** when the student arrives; **check out** when leaving (this frees the bed); **Cancel** to free a bed and reopen the application.
- **Payments** — confirm genuine payments (this confirms accommodation on the student's dashboard) or reject fake/incorrect ones.
- **Maintenance** — *Start* to move a request to in-progress, then *Resolve* with an optional note; the student is notified.
- **Reports** — occupancy by hostel, free-bed vacancy list, payment totals by method and semester, allocation register; CSV downloads for spreadsheets.

## 4. For university management (read-only)

- **Overview** — occupancy, free beds, applications awaiting the office, and confirmed payment totals.
- **Reports** — the full reports page with CSV exports, plus **Allocations** and **Availability** views.
- Management cannot modify records — screens are monitoring only.

## 5. Composition of statuses (quick reference)

| Object | Statuses |
|---|---|
| Student account | unverified → verified |
| Application | pending → under_review → approved / rejected → allocated |
| Bed | available / occupied / maintenance |
| Allocation | allocated → checked_in → checked_out (or cancelled) |
| Payment | pending → confirmed / failed |
| Maintenance | submitted → in_progress → resolved |

## 6. Troubleshooting

| Symptom | Cause & fix |
|---|---|
| "Your account must be verified before applying" | Office has not verified you yet — contact the hostel office. |
| "you already have an active application" | You can hold only one — wait for review of the current one. |
| Cannot delete hostel/room | It still has occupied beds; move residents out first. |
| Bed dropdown empty | No free beds — mark a bed `available` or free an allocation. |
| "application status must be approved" (API) | Allocate only after an application is approved. |
