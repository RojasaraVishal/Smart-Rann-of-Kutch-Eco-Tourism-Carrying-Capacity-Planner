"""
AGENT 2 — Sustainable Itinerary Recommendation Agent

Creates personalized, sustainable 1–7 day itineraries for Kutch.
Avoids overloaded destinations. Promotes lesser-known sites + artisan experiences.
DATA LABEL: AI
"""
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from models.models import (
    Destination, TouristProfile, Itinerary, ItineraryDestination,
    DestinationStatus, DestinationCategory
)
from agents.carrying_capacity_agent import calculate_for_destination
from agents.community_linkage_agent import match_community_experiences
from ml.carrying_capacity_model import compute_sustainability_score


# Slots per day: morning / afternoon / evening
DAILY_SLOTS = ["morning", "afternoon", "evening"]

INTEREST_TO_CATEGORY = {
    "desert": [DestinationCategory.desert, DestinationCategory.nature],
    "wildlife": [DestinationCategory.wildlife],
    "culture": [DestinationCategory.culture, DestinationCategory.heritage],
    "heritage": [DestinationCategory.heritage, DestinationCategory.culture],
    "handicraft": [DestinationCategory.handicraft, DestinationCategory.village],
    "village": [DestinationCategory.village, DestinationCategory.community],
    "adventure": [DestinationCategory.adventure, DestinationCategory.nature],
    "photography": [DestinationCategory.photography, DestinationCategory.nature],
    "nature": [DestinationCategory.nature, DestinationCategory.wildlife],
}

# Restricted/critical statuses — skip unless no alternatives
AVOID_STATUSES = {DestinationStatus.temporarily_closed, DestinationStatus.restricted}
SOFT_AVOID_STATUSES = {DestinationStatus.encourage_alternatives}


def generate_itinerary(
    db: Session,
    tourist_profile_id: int,
    start_date: datetime,
    duration_days: int,
    interests: List[str],
    budget: str = "moderate",
    group_size: int = 2,
) -> dict:
    """
    Generate a sustainable multi-day itinerary.
    """
    duration_days = max(1, min(duration_days, 7))
    all_destinations = db.query(Destination).filter(Destination.is_active == True).all()

    # Score each destination
    dest_scores = []
    for dest in all_destinations:
        if dest.current_status in AVOID_STATUSES:
            continue  # Hard skip
        cc = calculate_for_destination(db, dest.id)
        is_soft_avoid = dest.current_status in SOFT_AVOID_STATUSES or cc["pressure_level"] in ["high", "critical"]

        # Interest match
        relevant_cats = []
        for interest in interests:
            relevant_cats.extend(INTEREST_TO_CATEGORY.get(interest.lower(), []))
        interest_match = 1.0 if dest.category in relevant_cats else 0.3

        # Prefer lower pressure
        pressure_score = 1.0 - (cc["score"] / 100.0)

        # Community bonus
        community_bonus = 0.15 if dest.community_opportunities else 0.0

        # Popularity (balanced — not just highest)
        popularity_balance = 1.0 - abs(dest.popularity_score - 6.5) / 6.5

        composite = (
            interest_match * 0.35
            + pressure_score * 0.30
            + community_bonus
            + popularity_balance * 0.20
        )
        if is_soft_avoid:
            composite *= 0.6  # Penalise but don't fully exclude

        dest_scores.append((composite, dest, cc))

    dest_scores.sort(key=lambda x: x[0], reverse=True)
    # Take top destinations, avoid repeating same one
    selected = []
    used_ids = set()
    for score, dest, cc in dest_scores:
        if dest.id not in used_ids and len(selected) < duration_days * 2:
            selected.append((score, dest, cc))
            used_ids.add(dest.id)

    # Build day schedule
    stops = []
    day = 1
    slot_idx = 0
    for score, dest, cc in selected:
        if day > duration_days:
            break
        slot = DAILY_SLOTS[slot_idx % len(DAILY_SLOTS)]
        reason = _build_reason(dest, cc, interests)
        stops.append({
            "day": day,
            "slot": slot,
            "destination": dest,
            "cc": cc,
            "reason": reason,
        })
        slot_idx += 1
        if slot_idx % len(DAILY_SLOTS) == 0:
            day += 1

    # Community experiences
    community_data = match_community_experiences(
        db, interests, budget, group_size, max_results=3
    )

    # Sustainability score
    avg_crowd = sum(s["cc"]["score"] / 100 for s in stops) / max(len(stops), 1)
    avg_eco = sum(s["destination"].ecological_sensitivity / 10 for s in stops) / max(len(stops), 1)
    has_community = any(s["destination"].community_opportunities for s in stops)
    total_dist = duration_days * 35  # rough km estimate
    sens_time = sum(
        s["destination"].recommended_duration_hours
        for s in stops if s["destination"].ecological_sensitivity > 7
    )

    sus = compute_sustainability_score(
        crowd_pressure=avg_crowd,
        environmental_sensitivity=avg_eco,
        travel_distance_km=total_dist,
        uses_local_transport=True,
        local_community_benefit=0.75 if has_community else 0.35,
        group_size=group_size,
        time_in_sensitive_areas_hrs=sens_time,
    )

    # Persist itinerary
    tourist = db.query(TouristProfile).filter(TouristProfile.id == tourist_profile_id).first()
    itin = Itinerary(
        tourist_id=tourist_profile_id if tourist else 1,
        title=f"{duration_days}-Day Sustainable Kutch Journey",
        start_date=start_date,
        end_date=start_date + timedelta(days=duration_days - 1),
        sustainability_score=sus["sustainability_score"],
        crowd_score=round((1 - avg_crowd) * 100, 1),
        local_benefit_score=75.0 if has_community else 40.0,
        total_distance_km=total_dist,
        data_label="AI",
    )
    db.add(itin)
    db.flush()

    for s in stops:
        stop_obj = ItineraryDestination(
            itinerary_id=itin.id,
            destination_id=s["destination"].id,
            day_number=s["day"],
            visit_time=s["slot"],
            suggested_duration_hours=s["destination"].recommended_duration_hours,
            reason=s["reason"],
            crowd_level=s["cc"]["pressure_level"],
            sustainability_note=s["cc"]["recommended_action"],
        )
        db.add(stop_obj)
    db.commit()
    db.refresh(itin)

    # Format response
    day_plans = {}
    for s in stops:
        d = s["day"]
        dest = s["destination"]
        if d not in day_plans:
            day_plans[d] = []
        day_plans[d].append({
            "time_slot": s["slot"],
            "destination_id": dest.id,
            "destination_name": dest.name,
            "category": dest.category.value,
            "latitude": dest.latitude,
            "longitude": dest.longitude,
            "duration_hours": dest.recommended_duration_hours,
            "reason": s["reason"],
            "crowd_level": s["cc"]["pressure_level"],
            "carrying_capacity_score": s["cc"]["score"],
            "ecological_sensitivity": dest.ecological_sensitivity,
            "sustainable_practices": dest.sustainable_practices,
            "community_opportunities": dest.community_opportunities,
        })

    return {
        "data_label": "AI",
        "itinerary_id": itin.id,
        "title": itin.title,
        "start_date": start_date.isoformat(),
        "duration_days": duration_days,
        "sustainability_score": sus["sustainability_score"],
        "sustainability_label": sus["label"],
        "sustainability_reasons": sus["reasons"],
        "day_by_day": day_plans,
        "recommended_community_experiences": community_data["matched_experiences"][:3],
        "total_stops": len(stops),
        "parameters": {
            "interests": interests,
            "budget": budget,
            "group_size": group_size,
        },
        "important_note": (
            "This itinerary is AI-generated based on current platform data. "
            "Carrying capacity scores and tourist loads are model estimates, not official data. "
            "Always verify opening hours and permit requirements before visiting."
        ),
    }


def _build_reason(dest, cc: dict, interests: List[str]) -> str:
    reasons = []
    if cc["pressure_level"] in ["low", "moderate"]:
        reasons.append(f"lower visitor pressure ({cc['pressure_level']})")
    if dest.community_opportunities:
        reasons.append("local community tourism opportunities")
    if dest.ecological_sensitivity < 5:
        reasons.append("low ecological sensitivity")
    cat = dest.category.value
    if any(cat in INTEREST_TO_CATEGORY.get(i.lower(), []) for i in interests):
        reasons.append(f"matches your interest in {cat}")
    if not reasons:
        reasons.append("well-suited for a balanced Kutch itinerary")
    return f"Selected for: {'; '.join(reasons)}."
