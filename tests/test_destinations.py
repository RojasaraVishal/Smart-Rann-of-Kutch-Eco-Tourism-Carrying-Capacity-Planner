"""
Tests for destination and tourist load endpoints.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from database import Base, get_db
from main import app
from models.models import Destination, DestinationCategory, DestinationStatus

# Use a unique DB per module to avoid cross-module isolation issues
TEST_DATABASE_URL = "sqlite:///./test_dests2.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


def override_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


# Re-apply override at session scope so other modules' overrides don't displace it
@pytest.fixture(autouse=True, scope="session")
def apply_db_override():
    app.dependency_overrides[get_db] = override_db
    yield
    app.dependency_overrides.pop(get_db, None)


app.dependency_overrides[get_db] = override_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def seed_destinations():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSession()
    dests = [
        Destination(
            name="White Rann, Dhordo", latitude=23.888, longitude=69.875,
            category=DestinationCategory.desert, estimated_capacity=3000,
            current_load=2500, ecological_sensitivity=8.5,
            water_pressure=0.8, waste_pressure=0.75, infrastructure_capacity=0.85,
            current_status=DestinationStatus.encourage_alternatives,
        ),
        Destination(
            name="Kalo Dungar", latitude=23.995, longitude=69.691,
            category=DestinationCategory.nature, estimated_capacity=800,
            current_load=200, ecological_sensitivity=7.0,
            water_pressure=0.4, waste_pressure=0.35, infrastructure_capacity=0.45,
            current_status=DestinationStatus.open,
        ),
    ]
    for d in dests:
        db.add(d)
    db.commit()
    db.close()


# ── Destinations ──────────────────────────────────────────────────────────────

def test_list_destinations():
    r = client.get("/destinations/")
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 2


def test_get_destination_by_id():
    dests = client.get("/destinations/").json()
    first_id = dests[0]["id"]
    r = client.get(f"/destinations/{first_id}")
    assert r.status_code == 200
    assert "name" in r.json()


def test_destination_not_found():
    r = client.get("/destinations/9999")
    assert r.status_code == 404


def test_filter_by_category():
    r = client.get("/destinations/?category=desert")
    assert r.status_code == 200
    for d in r.json():
        assert d["category"] == "desert"


def test_filter_invalid_category():
    r = client.get("/destinations/?category=unicorn")
    assert r.status_code == 400


# ── Tourist Load ──────────────────────────────────────────────────────────────

def test_forecast_all():
    r = client.get("/tourist-load/forecast")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_forecast_destination():
    dests = client.get("/destinations/").json()
    dest_id = dests[0]["id"]
    r = client.get(f"/tourist-load/forecast/{dest_id}?days=1")
    assert r.status_code == 200
    data = r.json()
    assert "predicted_visitors" in data
    assert data["data_label"] == "PREDICTED"
    assert "note" in data  # Safety disclaimer present


def test_forecast_multi_day():
    dests = client.get("/destinations/").json()
    dest_id = dests[0]["id"]
    r = client.get(f"/tourist-load/forecast/{dest_id}?days=7")
    assert r.status_code == 200
    data = r.json()
    assert "days" in data
    assert len(data["days"]) == 7


def test_train_model():
    r = client.post("/tourist-load/train")
    assert r.status_code == 200
    data = r.json()
    assert "status" in data
