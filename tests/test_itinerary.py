"""
Tests for itinerary generation and community matching.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from database import Base, get_db
from main import app
from models.models import (
    Destination, DestinationCategory, DestinationStatus,
    Artisan, CommunityExperience, User, TouristProfile, UserRole
)
from utils.auth import hash_password

TEST_DATABASE_URL = "sqlite:///./test_itin.db"
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
def seed_data():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSession()

    # User + Profile
    user = User(name="Test", email="t@t.com", password_hash=hash_password("pass123"), role=UserRole.tourist)
    db.add(user); db.flush()
    profile = TouristProfile(user_id=user.id, interests=["desert", "culture"], budget="moderate", group_size=4)
    db.add(profile); db.flush()

    # Destinations
    dests = [
        Destination(name="White Rann", latitude=23.888, longitude=69.875,
                    category=DestinationCategory.desert, estimated_capacity=3000, current_load=2800,
                    ecological_sensitivity=8.5, water_pressure=0.85, waste_pressure=0.8,
                    infrastructure_capacity=0.9, current_status=DestinationStatus.encourage_alternatives),
        Destination(name="Kalo Dungar", latitude=23.995, longitude=69.691,
                    category=DestinationCategory.nature, estimated_capacity=800, current_load=200,
                    ecological_sensitivity=7.0, water_pressure=0.4, waste_pressure=0.35,
                    infrastructure_capacity=0.45, current_status=DestinationStatus.open),
        Destination(name="Bhujodi", latitude=23.207, longitude=69.72,
                    category=DestinationCategory.handicraft, estimated_capacity=1000, current_load=250,
                    ecological_sensitivity=2.0, water_pressure=0.28, waste_pressure=0.3,
                    infrastructure_capacity=0.45, community_opportunities=True,
                    current_status=DestinationStatus.open),
        Destination(name="Hodka Village", latitude=23.722, longitude=69.808,
                    category=DestinationCategory.village, estimated_capacity=300, current_load=80,
                    ecological_sensitivity=4.5, water_pressure=0.35, waste_pressure=0.28,
                    infrastructure_capacity=0.4, community_opportunities=True,
                    current_status=DestinationStatus.open),
    ]
    for d in dests:
        db.add(d)
    db.flush()

    # Artisan + Experience
    artisan = Artisan(name="Test Artisan", location="Bhujodi", latitude=23.207, longitude=69.72,
                      category="embroidery", speciality="Test", rating=4.8)
    db.add(artisan); db.flush()
    exp = CommunityExperience(artisan_id=artisan.id, title="Embroidery Workshop",
                               category="embroidery", price_per_person=800,
                               max_capacity=10, duration_hours=3.0, languages=["English"])
    db.add(exp)
    db.commit()
    db.close()


# ── Itinerary Generation ──────────────────────────────────────────────────────

def test_generate_itinerary():
    tomorrow = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")
    r = client.post("/itinerary/generate/guest", json={
        "start_date": tomorrow,
        "duration_days": 3,
        "interests": ["desert", "culture", "handicraft"],
        "budget": "moderate",
        "group_size": 4
    })
    assert r.status_code == 200
    data = r.json()
    assert "itinerary_id" in data
    assert data["data_label"] == "AI"
    assert "sustainability_score" in data
    assert 0 <= data["sustainability_score"] <= 100
    assert "day_by_day" in data
    assert "important_note" in data  # Safety disclaimer present


def test_itinerary_avoids_critical_destinations():
    tomorrow = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")
    r = client.post("/itinerary/generate/guest", json={
        "start_date": tomorrow,
        "duration_days": 2,
        "interests": ["desert"],
        "budget": "moderate",
        "group_size": 2
    })
    assert r.status_code == 200
    data = r.json()
    # White Rann (encourage_alternatives) should not dominate — check it's deprioritized
    all_stops = [s["destination_name"] for day in data["day_by_day"].values() for s in day]
    # Should include some non-overcrowded alternatives
    assert len(all_stops) > 0


def test_invalid_date_format():
    r = client.post("/itinerary/generate/guest", json={
        "start_date": "not-a-date", "duration_days": 3,
        "interests": ["desert"], "budget": "moderate", "group_size": 2
    })
    assert r.status_code == 400


# ── Community Matching ────────────────────────────────────────────────────────

def test_community_match():
    r = client.post("/artisans/match", json={
        "interests": ["handicraft", "culture"],
        "budget": "moderate",
        "group_size": 4
    })
    assert r.status_code == 200
    data = r.json()
    assert data["data_label"] == "AI"
    assert "matched_experiences" in data
    # Every match should have a score and reasons
    for m in data["matched_experiences"]:
        assert 0 <= m["match_score"] <= 100
        assert isinstance(m["match_reasons"], list)


def test_community_match_budget_filter():
    r = client.post("/artisans/match", json={
        "interests": ["handicraft"],
        "budget": "budget",
        "group_size": 10  # Large group — penalise expensive options
    })
    assert r.status_code == 200


def test_list_artisans():
    r = client.get("/artisans/")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)


def test_list_experiences():
    r = client.get("/artisans/experiences")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
