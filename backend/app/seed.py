"""
UniNest demo data seeder.

Usage:
    cd backend && .venv/bin/python -m app.seed
"""

import itertools
from datetime import date, datetime

from app import create_app
from app.extensions import db
from app.models import (
    User,
    Student,
    Hostel,
    Room,
    Bed,
    Application,
    Allocation,
    Payment,
    MaintenanceRequest,
    Notification,
)


def seed():
    app = create_app()
    with app.app_context():
        if User.query.first():
            print("database already contains data; seeding skipped")
            return

        admin = User(email="admin@uninest.ac.ke", full_name="Asha Kariuki", role="admin")
        admin.set_password("Admin@123")
        management = User(email="management@uninest.ac.ke", full_name="Dr. Peter Wambua", role="management")
        management.set_password("Manage@123")
        db.session.add_all([admin, management])

        demo_students = [
            ("miriam.otieno@student.ac.ke", "Miriam Otieno", "25/01011", "BSc Computer Science", 2, "female", "verified"),
            ("brian.kimani@student.ac.ke", "Brian Kimani", "25/03338", "BSc Software Engineering", 1, "male", "verified"),
            ("faith.wanjiku@student.ac.ke", "Faith Wanjiku", "25/01472", "BA Economics", 3, "female", "unverified"),
            ("david.mwenda@student.ac.ke", "David Mwenda", "25/02987", "BSc Civil Engineering", 2, "male", "verified"),
        ]

        students = []
        for email, name, reg, program, year, gender, status in demo_students:
            u = User(email=email, full_name=name, role="student")
            u.set_password("Student@123")
            s = Student(
                registration_no=reg,
                program=program,
                year_of_study=year,
                gender=gender,
                verification_status=status,
                phone=f"070{len(students)}2345{len(students)}6",
            )
            u.student = s
            db.session.add(u)
            students.append(s)

        hostels = [
            Hostel(name="Nanyuki Hall", gender="female", location="North Campus", description="Quiet riverside Students' hostel"),
            Hostel(name="Eldoret Wing", gender="male", location="South Campus", description="Close to the engineering block"),
        ]
        db.session.add_all(hostels)

        counter = itertools.count(1)
        allocations_planned = []
        for hostel in hostels:
            for floor in (1, 2):
                for rnum in (1, 2, 3):
                    room = Room(hostel=hostel, number=f"{floor}{rnum:02d}", floor=floor, room_type="shared")
                    db.session.add(room)
                    db.session.flush()
                    for _ in range(4):
                        db.session.add(Bed(room=room, bed_number=str(next(counter) % 4 + 1)))

        db.session.flush()

        nanyuki = hostels[0] if hostels[0].name == "Nanyuki Hall" else hostels[1]
        eldoret = hostels[1]

        verified_f = [s for s in students if s.verification_status == "verified" and s.gender == "female"]
        verified_m = [s for s in students if s.verification_status == "verified" and s.gender == "male"]

        plan = [
            (verified_f[0], nanyuki),
            ((verified_m or [verified_f[1]])[0], eldoret),
        ]
        for student, hostel in plan:
            app_row = Application(
                student=student,
                preferred_hostel=hostel,
                room_preference="any",
                status="approved",
                review_notes="Documents verified",
            )
            db.session.add(app_row)
            allocations_planned.append((student, hostel, app_row))

        db.session.flush()

        for student, hostel, app_row in allocations_planned:
            bed = Bed.query.join(Room).filter(Room.hostel_id == hostel.id, Bed.status == "available").first()
            if not bed:
                continue
            bed.status = "occupied"
            allocation = Allocation(
                student=student,
                bed=bed,
                application=app_row,
                status="checked_in",
                check_in_date=date.today(),
                allocated_by=1,
            )
            db.session.add(allocation)
            db.session.flush()
            pay = Payment(
                reference=f"UNI-SEED-{allocation.id:04d}",
                student=student,
                allocation=allocation,
                amount=14500.0,
                method="mpesa",
                status="confirmed",
                confirmed_at=datetime.utcnow(),
                description="Hostel accommodation fee",
            )
            db.session.add(pay)
            allocation.paid = True
            allocation.accommodation_confirmed = True

            db.session.add(
                Notification(
                    user_id=student.user_id,
                    type="allocation",
                    title="Room allocated",
                    message=f"You have been allocated bed {bed.bed_number} in room {bed.room.number}, {bed.room.hostel.name}.",
                    is_read=True,
                )
            )

        pending_student = students[2]
        pending_hostel = nanyuki
        if pending_student.verification_status != "verified":
            db.session.add(
                Application(student=pending_student, preferred_hostel=pending_hostel, room_preference="shared", status="pending")
            )

        allocated_holder = students[3] if len(students) > 3 else students[0]
        problem_app = Application(
            student=allocated_holder if allocated_holder.verification_status == "verified" else students[0],
            preferred_hostel=eldoret,
            room_preference="single",
            status="pending",
            notes="Requested ground floor for medical reasons",
        )
        db.session.add(problem_app)

        first_alloc = Allocation.query.first()
        if first_alloc:
            mreq = MaintenanceRequest(
                allocation=first_alloc,
                student=first_alloc.student,
                title="Leaking tap",
                description="The bathroom tap in my room is leaking and the floor stays wet.",
                priority="medium",
                status="submitted",
            )
            db.session.add(mreq)

        db.session.commit()
        print("seeded:")
        print("  admin       admin@uninest.ac.ke / Admin@123")
        print("  management  management@uninest.ac.ke / Manage@123")
        print("  students    miriam.otieno@student.ac.ke, brian.kimani@student.ac.ke, faith.wanjiku@student.ac.ke, david.mwenda@student.ac.ke / Student@123")
        print(f"  hostels     {Hostel.query.count()} | rooms {Room.query.count()} | beds {Bed.query.count()}")
        print(f"  applications {Application.query.count()} | allocations {Allocation.query.count()} | payments {Payment.query.count()}")


if __name__ == "__main__":
    seed()
