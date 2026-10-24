import os

os.environ.setdefault("DATABASE_URL", "mysql+pymysql://u:p@127.0.0.1:3306/test")
os.environ.setdefault("JWT_SECRET", "x" * 40)

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base, get_db
from app.main import app
from app.models import AdminUser
from app.security import hash_password


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with Session() as s:
        s.add(AdminUser(email="admin@example.com", password_hash=hash_password("Secret123!")))
        s.commit()

    def override():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def event_body(**kw):
    start = datetime.now(timezone.utc) + timedelta(days=5)
    body = {
        "title": "Portfolio Workshop", "description": "x", "category": "Workshop",
        "starts_at": start.isoformat(), "ends_at": (start + timedelta(hours=3)).isoformat(),
        "venue": "Studio 04, Pune", "capacity": 1, "status": "upcoming",
    }
    body.update(kw)
    return body


def login(c):
    r = c.post("/api/auth/login", json={"email": "admin@example.com", "password": "Secret123!"})
    assert r.status_code == 200, r.text
    return r


def test_admin_requires_login(client):
    assert client.get("/api/admin/dashboard").status_code == 401
    assert client.get("/api/auth/me").status_code == 401


def test_bad_login(client):
    r = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "nope"})
    assert r.status_code == 401


def test_full_flow(client):
    r = login(client)
    assert "httponly" in r.headers["set-cookie"].lower()
    assert client.get("/api/auth/me").json() == {"email": "admin@example.com"}

    created = client.post("/api/admin/events", json=event_body())
    assert created.status_code == 201, created.text
    eid = created.json()["id"]

    pub = client.get("/api/events", params={"category": "All", "sort": "date"}).json()
    assert len(pub) == 1 and pub[0]["available_seats"] == 1

    reg = {"full_name": "Tanay Pusalkar", "email": "t@example.com", "contact_number": "8707908908"}
    assert client.post(f"/api/events/{eid}/registrations", json=reg).status_code == 201
    assert client.get(f"/api/events/{eid}").json()["available_seats"] == 0

    dup = client.post(f"/api/events/{eid}/registrations", json=reg)
    assert dup.status_code == 409
    other = {**reg, "email": "other@example.com"}
    assert client.post(f"/api/events/{eid}/registrations", json=other).status_code == 409  # full

    assert client.get(f"/api/admin/events/{eid}/registrations").json()[0]["email"] == "t@example.com"
    assert client.get("/api/admin/dashboard").json()["total_registrations"] == 1
    assert client.patch(f"/api/admin/events/{eid}", json={"capacity": 0}).status_code == 409
    assert client.patch(f"/api/admin/events/{eid}", json={"status": "completed"}).status_code == 200
    assert client.delete(f"/api/admin/events/{eid}").status_code == 204

    assert client.post("/api/auth/logout").status_code == 204
    client.cookies.clear()
    assert client.get("/api/admin/dashboard").status_code == 401


def test_db_health(client):
    assert client.get("/api/health/db").json()["database"] == "connected"
