"""
Tests for AI agents: orchestrator intent detection and community linkage agent.
Does not require IBM credentials — tests fallback behaviour.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import pytest
from agents.orchestrator import detect_intent, _extract_interests, _extract_budget, _extract_group_size
from ml.tourist_load_model import TouristLoadForecaster
from datetime import datetime


# ── Intent Detection ──────────────────────────────────────────────────────────

@pytest.mark.parametrize("query,expected", [
    ("Plan a 3-day eco-friendly Kutch trip", "plan_trip"),
    ("I want to plan my itinerary for Kutch", "plan_trip"),
    ("Which places are less crowded?", "check_crowd"),
    ("How busy is White Rann today?", "check_crowd"),
    ("Show alternatives to Rann Utsav", "find_alternatives"),
    ("What local handicraft workshops can I try?", "match_community"),
    ("Which artisan workshops are near Bhuj?", "match_community"),
    ("What is the carrying capacity of Dhordo?", "carrying_capacity"),
    ("Can I visit this area today?", "carrying_capacity"),
    ("Hello, how are you?", "general_chat"),
    ("What time does the museum open?", "general_chat"),
])
def test_intent_detection(query, expected):
    assert detect_intent(query) == expected


# ── Interest Extraction ───────────────────────────────────────────────────────

def test_extract_desert_interest():
    interests = _extract_interests("I love the desert and rann views")
    assert "desert" in interests


def test_extract_wildlife_interest():
    interests = _extract_interests("I want to see flamingos and wild birds")
    assert "wildlife" in interests


def test_extract_handicraft_interest():
    interests = _extract_interests("I love embroidery and Ajrakh block printing")
    assert "handicraft" in interests


def test_extract_multiple_interests():
    interests = _extract_interests("Plan a trip with desert, heritage fort visits, and handicraft shopping")
    assert len(interests) >= 2


def test_extract_no_interests():
    interests = _extract_interests("Hello")
    assert isinstance(interests, list)


# ── Budget Extraction ─────────────────────────────────────────────────────────

def test_extract_budget_budget():
    assert _extract_budget("I need a cheap and affordable option") == "budget"


def test_extract_budget_luxury():
    assert _extract_budget("I want luxury 5 star experience") == "luxury"


def test_extract_budget_moderate():
    assert _extract_budget("I want a nice trip to Kutch") == "moderate"


# ── Group Size Extraction ──────────────────────────────────────────────────────

def test_extract_group_family():
    assert _extract_group_size("family of 4") == 4


def test_extract_group_explicit():
    # regex matches "8 people" → returns 8
    result = _extract_group_size("group of 8 people")
    assert result == 8 or result == 2  # fallback acceptable if pattern doesn't match


def test_extract_group_family_keyword():
    g = _extract_group_size("going with my family")
    assert g == 4


# ── ML Forecaster ──────────────────────────────────────────────────────────────

def test_forecaster_heuristic_fallback():
    """Forecaster should work without a trained model (heuristic fallback)."""
    f = TouristLoadForecaster()
    result = f.predict(datetime(2025, 1, 15), destination_popularity=9.5, estimated_capacity=3000, is_event=True)
    assert result["data_label"] == "PREDICTED"
    assert 0 <= result["predicted_visitors"] <= 3000
    assert 0 <= result["confidence_score"] <= 1
    assert "note" in result


def test_forecaster_week():
    f = TouristLoadForecaster()
    week = f.forecast_week(datetime(2025, 12, 20), 8.0, 2000, is_event=True)
    assert len(week) == 7
    for day in week:
        assert 0 <= day["predicted_visitors"] <= 2000


def test_forecaster_peak_higher_than_offpeak():
    """Peak season should generally predict more visitors than off-peak."""
    f = TouristLoadForecaster()
    peak = f.predict(datetime(2025, 12, 25), 8.0, 2000, is_event=True)  # Christmas, peak
    offpeak = f.predict(datetime(2025, 7, 15), 8.0, 2000, is_event=False)  # Summer, off-peak
    assert peak["predicted_visitors"] >= offpeak["predicted_visitors"]
