"""
AGENT 3 — Ecological Carrying Capacity Agent

Estimates whether a destination can safely accommodate more tourists.
DATA LABEL: PREDICTED — model estimates only, NOT official ecological limits.
"""
from datetime import datetime
from sqlalchemy.orm import Session
from models.models import Destination, EcologicalMetric, CarryingCapacity, PressureLevel, DestinationStatus
from ml.carrying_capacity_model import compute_carrying_capacity


def calculate_for_destination(db: Session, destination_id: int) -> dict:
    """
    Calculate current carrying capacity for a destination and persist the result.
    """
    dest = db.query(Destination).filter(Destination.id == destination_id).first()
    if not dest:
        return {"error": f"Destination {destination_id} not found"}

    # Use latest ecological metrics if available, else fall back to destination defaults
    latest_metric = (
        db.query(EcologicalMetric)
        .filter(EcologicalMetric.destination_id == destination_id)
        .order_by(EcologicalMetric.date.desc())
        .first()
    )

    water_stress = latest_metric.water_stress if latest_metric else dest.water_pressure
    waste_stress = latest_metric.waste_stress if latest_metric else dest.waste_pressure
    infra_stress = latest_metric.infrastructure_stress if latest_metric else dest.infrastructure_capacity
    eco_sensitivity = dest.ecological_sensitivity

    result = compute_carrying_capacity(
        current_visitors=dest.current_load,
        estimated_capacity=dest.estimated_capacity,
        water_stress=water_stress,
        waste_stress=waste_stress,
        infrastructure_stress=infra_stress,
        ecological_sensitivity=eco_sensitivity,
    )

    # Persist to DB
    cc = CarryingCapacity(
        destination_id=destination_id,
        score=result["score"],
        pressure_level=PressureLevel(result["pressure_level"]),
        status=DestinationStatus(result["status"]),
        tourist_load_pct=result["tourist_load_pct"],
        water_stress=result["water_stress"],
        waste_stress=result["waste_stress"],
        infrastructure_stress=result["infrastructure_stress"],
        ecological_risk=result["ecological_risk_pct"],
        recommended_action=result["recommended_action"],
        calculated_at=datetime.utcnow(),
        data_label="PREDICTED",
    )
    db.add(cc)
    db.commit()

    return {
        **result,
        "destination_id": dest.id,
        "destination_name": dest.name,
        "latitude": dest.latitude,
        "longitude": dest.longitude,
        "category": dest.category.value,
        "current_load": dest.current_load,
        "estimated_capacity": dest.estimated_capacity,
    }


def get_all_carrying_capacities(db: Session) -> list:
    """Calculate and return carrying capacity for every active destination."""
    destinations = db.query(Destination).filter(Destination.is_active == True).all()
    return [calculate_for_destination(db, d.id) for d in destinations]


def find_alternatives(db: Session, destination_id: int, max_alternatives: int = 3) -> dict:
    """
    When a destination is overloaded, find similar alternatives with lower pressure.
    Returns: {overloaded_dest, alternatives: []}
    """
    overloaded = db.query(Destination).filter(Destination.id == destination_id).first()
    if not overloaded:
        return {"error": "Destination not found"}

    cc_overloaded = calculate_for_destination(db, destination_id)

    # All other destinations in same or similar category
    all_dests = (
        db.query(Destination)
        .filter(Destination.id != destination_id, Destination.is_active == True)
        .all()
    )

    candidates = []
    for d in all_dests:
        cc = calculate_for_destination(db, d.id)
        if cc.get("score", 100) < cc_overloaded.get("score", 0) - 15:  # significantly less pressure
            # Compute rough similarity score
            same_cat = 1.0 if d.category == overloaded.category else 0.4
            # Prefer community_opportunities
            community = 0.2 if d.community_opportunities else 0.0
            score_diff_bonus = max(0, (cc_overloaded["score"] - cc["score"]) / 100)
            similarity = round((same_cat * 0.5 + score_diff_bonus * 0.3 + community + 0.1) * 100, 1)
            candidates.append({
                "destination": d,
                "cc": cc,
                "similarity_score": min(similarity, 98),
            })

    # Sort by CC score ascending (lowest pressure first) then slice
    candidates.sort(key=lambda x: x["cc"]["score"])
    top = candidates[:max_alternatives]

    alternatives = []
    for c in top:
        d = c["destination"]
        alternatives.append({
            "destination_id": d.id,
            "name": d.name,
            "category": d.category.value,
            "latitude": d.latitude,
            "longitude": d.longitude,
            "carrying_capacity_score": c["cc"]["score"],
            "pressure_level": c["cc"]["pressure_level"],
            "similarity_score": c["similarity_score"],
            "reason": (
                f"{d.name} offers a {'similar' if d.category == overloaded.category else 'complementary'} "
                f"experience with significantly lower tourism pressure "
                f"({c['cc']['score']:.0f} vs {cc_overloaded['score']:.0f})."
            ),
            "community_opportunities": d.community_opportunities,
            "current_status": d.current_status.value,
        })

    return {
        "data_label": "AI",
        "overloaded_destination": {
            "destination_id": overloaded.id,
            "name": overloaded.name,
            "carrying_capacity_score": cc_overloaded["score"],
            "pressure_level": cc_overloaded["pressure_level"],
            "recommended_action": cc_overloaded["recommended_action"],
        },
        "alternatives": alternatives,
        "message": (
            f"'{overloaded.name}' is currently experiencing {cc_overloaded['pressure_level'].upper()} tourism pressure "
            f"(score: {cc_overloaded['score']:.0f}/100). "
            f"Consider these {len(alternatives)} alternative destinations that offer similar experiences "
            f"with lower visitor load."
        ) if alternatives else f"No suitable low-pressure alternatives found for '{overloaded.name}' at this time.",
    }
