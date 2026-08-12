"""
Test suite for authentication endpoints.
Run: pytest tests/ -v
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, get_db
from main import app

# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite:///./test_kutch.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


def override_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


# ── Registration Tests ────────────────────────────────────────────────────────

def test_register_tourist():
    r = client.post("/auth/register", json={
        "name": "Test Tourist", "email": "test@test.com", "password": "pass123", "role": "tourist"
    })
    assert r.status_code == 201
    data = r.json()
    assert "access_token" in data
    assert data["role"] == "tourist"
    assert data["name"] == "Test Tourist"


def test_register_duplicate_email():
    client.post("/auth/register", json={"name": "A", "email": "dup@test.com", "password": "pass123", "role": "tourist"})
    r = client.post("/auth/register", json={"name": "B", "email": "dup@test.com", "password": "pass123", "role": "tourist"})
    assert r.status_code == 400
    assert "already registered" in r.json()["detail"].lower()


def test_register_short_password():
    r = client.post("/auth/register", json={"name": "A", "email": "a@a.com", "password": "12", "role": "tourist"})
    assert r.status_code == 422


def test_register_invalid_role():
    r = client.post("/auth/register", json={"name": "A", "email": "b@b.com", "password": "pass123", "role": "superuser"})
    assert r.status_code == 422


# ── Login Tests ───────────────────────────────────────────────────────────────

def test_login_success():
    client.post("/auth/register", json={"name": "A", "email": "login@test.com", "password": "pass123", "role": "tourist"})
    r = client.post("/auth/login", data={"username": "login@test.com", "password": "pass123"})
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_login_wrong_password():
    client.post("/auth/register", json={"name": "A", "email": "wp@test.com", "password": "pass123", "role": "tourist"})
    r = client.post("/auth/login", data={"username": "wp@test.com", "password": "wrongpass"})
    assert r.status_code == 401


def test_login_nonexistent_user():
    r = client.post("/auth/login", data={"username": "ghost@test.com", "password": "pass123"})
    assert r.status_code == 401
