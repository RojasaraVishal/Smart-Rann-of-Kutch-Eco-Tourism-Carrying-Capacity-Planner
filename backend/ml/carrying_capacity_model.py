"""
Ecological Carrying Capacity Model.

Computes a weighted pressure score (0–100) for each destination.
Weights are configurable by admin via Settings.

DATA LABEL: PREDICTED — model estimates only, not official ecological limits.
Formula:
  Score = 100 * (
      w_tourist_load  * tourist_load_ratio +
      w_water_stress  * water_stress +
      w_waste_stress  * waste_stress +
      w_infra         * infrastructure_stress +
      w_ecological    * ecological_risk_norm
  )

All inputs normalized to [0, 1].
"""
from config import get_settings

settings = get_settings()


def compute_carrying_capacity(
    current_visitors: int,
    estimated_capacity: int,
    water_stress: float,        # 0–1
    waste_stress: float,        # 0–1
    infrastructure_stress: float,  # 0–1 (1 = fully stressed)
    ecological_sensitivity: float,  # 1–10 scale from destination record
    weights: dict = None,
) -> dict:
    """
    Compute carrying capacity pressure score.

    Args:
        weights: optional dict overriding default weights
    Returns:
        Full scoring breakdown dict with data_label = PREDICTED
    """
    w = weights or {
        "tourist_load": settings.cc_weight_tourist_load,
        "water_stress": settings.cc_weight_water_stress,
        "waste_stress": settings.cc_weight_waste_stress,
        "infrastructure": settings.cc_weight_infrastructure,
        "ecological_risk": settings.cc_weight_ecological_risk,
    }

    # Normalise tourist load to 0–1
    tourist_load_ratio = min(current_visitors / max(estimated_capacity, 1), 1.0)

    # Normalise ecological sensitivity 1–10 → 0–1
    ecological_risk_norm = (ecological_sensitivity - 1) / 9.0

    # Clamp all values
    water = max(0.0, min(1.0, water_stress))
    waste = max(0.0, min(1.0, waste_stress))
    infra = max(0.0, min(1.0, infrastructure_stress))
    eco = max(0.0, min(1.0, ecological_risk_norm))
    tl = max(0.0, min(1.0, tourist_load_ratio))

    score = 100.0 * (
        w["tourist_load"] * tl
        + w["water_stress"] * water
        + w["waste_stress"] * waste
        + w["infrastructure"] * infra
        + w["ecological_risk"] * eco
    )
    score = round(min(score, 100.0), 1)

    # Classify
    low_t = settings.cc_low_threshold
    mod_t = settings.cc_moderate_threshold
    high_t = settings.cc_high_threshold

    if score <= low_t:
        pressure_level = "low"
        status = "open"
        recommended_action = "Normal visitation. Sustainable tourism practices encouraged."
        color = "#22c55e"
    elif score <= mod_t:
        pressure_level = "moderate"
        status = "normal"
        recommended_action = "Monitor closely. Encourage visitors to spread across visit times."
        color = "#f59e0b"
    elif score <= high_t:
        pressure_level = "high"
        status = "encourage_alternatives"
        recommended_action = "Encourage alternative destinations. Avoid additional large group bookings."
        color = "#f97316"
    else:
        pressure_level = "critical"
        status = "restricted"
        recommended_action = "Restrict additional visitors. Consider temporary capacity limits or permit system."
        color = "#ef4444"

    return {
        "data_label": "PREDICTED",
        "score": score,
        "pressure_level": pressure_level,
        "status": status,
        "color": color,
        "tourist_load_pct": round(tourist_load_ratio * 100, 1),
        "water_stress": round(water * 100, 1),
        "waste_stress": round(waste * 100, 1),
        "infrastructure_stress": round(infra * 100, 1),
        "ecological_risk_pct": round(eco * 100, 1),
        "recommended_action": recommended_action,
        "weights_used": w,
        "disclaimer": (
            "This carrying capacity score is a model estimate for planning purposes only. "
            "It is NOT an official ecological limit set by any government or scientific body."
        ),
    }


def compute_sustainability_score(
    crowd_pressure: float,         # 0–1
    environmental_sensitivity: float,  # 0–1
    travel_distance_km: float,
    uses_local_transport: bool,
    local_community_benefit: float,  # 0–1
    group_size: int,
    time_in_sensitive_areas_hrs: float,
) -> dict:
    """
    Compute a sustainability score for an itinerary (0–100, higher = more sustainable).
    """
    # Invert pressure (lower pressure = more sustainable)
    crowd_factor = 1.0 - crowd_pressure
    env_factor = 1.0 - environmental_sensitivity
    # Distance score: penalise excessive travel (> 200 km)
    distance_factor = max(0, 1 - (travel_distance_km / 200))
    transport_factor = 0.9 if uses_local_transport else 0.6
    community_factor = local_community_benefit
    # Penalise large groups in sensitive areas
    group_factor = max(0.4, 1 - (group_size - 1) * 0.03)
    # Penalise long time in sensitive areas
    sensitivity_time_factor = max(0.3, 1 - (time_in_sensitive_areas_hrs * 0.08))

    score = 100 * (
        0.20 * crowd_factor
        + 0.20 * env_factor
        + 0.15 * distance_factor
        + 0.15 * transport_factor
        + 0.15 * community_factor
        + 0.10 * group_factor
        + 0.05 * sensitivity_time_factor
    )
    score = round(min(max(score, 0), 100), 1)

    reasons = []
    if crowd_pressure < 0.4:
        reasons.append("Avoids overcrowded destinations")
    if environmental_sensitivity < 0.4:
        reasons.append("Focuses on low-sensitivity areas")
    if local_community_benefit > 0.6:
        reasons.append("Strong local community engagement")
    if uses_local_transport:
        reasons.append("Uses sustainable/local transport")
    if travel_distance_km < 100:
        reasons.append("Compact travel route, low emissions")

    return {
        "data_label": "AI",
        "sustainability_score": score,
        "label": "Excellent" if score > 75 else "Good" if score > 55 else "Moderate" if score > 35 else "Low",
        "reasons": reasons,
    }
