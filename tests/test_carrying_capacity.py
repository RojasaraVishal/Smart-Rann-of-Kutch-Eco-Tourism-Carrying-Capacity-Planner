"""
Tests for carrying capacity agent and endpoint.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import pytest
from ml.carrying_capacity_model import compute_carrying_capacity, compute_sustainability_score


# ── Carrying Capacity Model Unit Tests ───────────────────────────────────────

def test_low_pressure_score():
    result = compute_carrying_capacity(
        current_visitors=100, estimated_capacity=1000,
        water_stress=0.2, waste_stress=0.2, infrastructure_stress=0.2,
        ecological_sensitivity=3.0
    )
    assert result["score"] < 40
    assert result["pressure_level"] == "low"
    assert result["status"] == "open"
    assert result["data_label"] == "PREDICTED"
    assert "disclaimer" in result  # Safety disclaimer always present


def test_critical_pressure_score():
    result = compute_carrying_capacity(
        current_visitors=1000, estimated_capacity=1000,
        water_stress=0.95, waste_stress=0.95, infrastructure_stress=0.95,
        ecological_sensitivity=9.5
    )
    assert result["score"] >= 80
    assert result["pressure_level"] == "critical"
    assert result["status"] == "restricted"


def test_score_bounded_0_to_100():
    """Score should never exceed 100 or go below 0."""
    r1 = compute_carrying_capacity(0, 1000, 0.0, 0.0, 0.0, 1.0)
    r2 = compute_carrying_capacity(9999, 1000, 1.0, 1.0, 1.0, 10.0)
    assert 0 <= r1["score"] <= 100
    assert 0 <= r2["score"] <= 100


def test_custom_weights():
    """Custom weights should sum to 1.0 and produce a valid score."""
    weights = {
        "tourist_load": 0.50, "water_stress": 0.15,
        "waste_stress": 0.15, "infrastructure": 0.10, "ecological_risk": 0.10
    }
    result = compute_carrying_capacity(
        current_visitors=500, estimated_capacity=1000,
        water_stress=0.5, waste_stress=0.5, infrastructure_stress=0.5,
        ecological_sensitivity=5.0, weights=weights
    )
    assert 0 <= result["score"] <= 100
    assert result["weights_used"] == weights


def test_moderate_pressure():
    result = compute_carrying_capacity(
        current_visitors=450, estimated_capacity=1000,
        water_stress=0.5, waste_stress=0.5, infrastructure_stress=0.5,
        ecological_sensitivity=5.0
    )
    assert result["pressure_level"] in ["moderate", "low", "high"]


# ── Sustainability Score Tests ────────────────────────────────────────────────

def test_sustainability_high():
    result = compute_sustainability_score(
        crowd_pressure=0.1, environmental_sensitivity=0.1,
        travel_distance_km=50, uses_local_transport=True,
        local_community_benefit=0.9, group_size=2,
        time_in_sensitive_areas_hrs=0.5
    )
    assert result["sustainability_score"] > 70
    assert result["label"] in ["Excellent", "Good"]
    assert result["data_label"] == "AI"


def test_sustainability_low():
    result = compute_sustainability_score(
        crowd_pressure=0.95, environmental_sensitivity=0.95,
        travel_distance_km=300, uses_local_transport=False,
        local_community_benefit=0.1, group_size=40,
        time_in_sensitive_areas_hrs=10
    )
    assert result["sustainability_score"] < 50


def test_sustainability_bounded():
    result = compute_sustainability_score(
        crowd_pressure=0.5, environmental_sensitivity=0.5,
        travel_distance_km=100, uses_local_transport=True,
        local_community_benefit=0.5, group_size=4,
        time_in_sensitive_areas_hrs=2
    )
    assert 0 <= result["sustainability_score"] <= 100
