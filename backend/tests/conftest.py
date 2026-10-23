import pytest

from app import create_app
from app.extensions import db as _db
from app.models import User
from config import TestConfig


@pytest.fixture
def app():
    app = create_app(TestConfig())
    with app.app_context():
        _db.session.remove()
        _db.drop_all()
        _db.create_all()

        admin = User(email="admin@test.ac.ke", full_name="Admin", role="admin")
        admin.set_password("Admin@123")
        student_user = User(email="stud@test.ac.ke", full_name="Stud", role="student")
        student_user.set_password("Stud@123")
        student_user.student and None
        from app.models import Student

        profile = Student(program="BSc CS", year_of_study=1)
        student_user.student = profile
        _db.session.add_all([admin, student_user])
        _db.session.commit()

        yield app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def tokens(client):
    admin = client.post("/api/auth/login", json={"email": "admin@test.ac.ke", "password": "Admin@123"}).get_json()["token"]
    student = client.post("/api/auth/login", json={"email": "stud@test.ac.ke", "password": "Stud@123"}).get_json()["token"]
    return {"admin": admin, "student": student}


def A(t):
    return {"Authorization": f"Bearer {t}"}
