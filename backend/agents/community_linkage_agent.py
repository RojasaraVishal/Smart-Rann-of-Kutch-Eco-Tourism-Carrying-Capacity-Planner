"""
AGENT 4 — Local Artisan & Community Linkage Agent

Matches tourists with local artisans, experiences, and community opportunities.
DATA LABEL: AI — recommendations generated from available platform data.
"""
from typing import List
from sqlalchemy.orm import Session
from models.models import Artisan, CommunityExperience, Destination


CATEGORY_INTEREST_MAP = {
    "embroidery": ["handicraft", "culture", "art"],
    "weaving": ["handicraft", "culture", "textile"],
    "music": ["culture", "performing_arts", "festival"],
    "printing": ["handicraft", "art", "culture"],
    "textile": ["handicraft", "culture", "fashion"],
    "mud_art": ["culture", "art", "architecture"],
    "heritage": ["heritage", "history", "culture"],
    "eco_tour": ["wildlife", "nature", "adventure", "photography"],
}

BUDGET_PRICE_MAP = {
    "budget": 600,
    "moderate": 1200,
    "luxury": 99999,
}


def match_community_experiences(
    db: Session,
    tourist_interests: List[str],
    budget: str = "moderate",
    group_size: int = 2,
    max_results: int = 5,
) -> dict:
    """
    Match tourist profile to community experiences.
    Returns experiences sorted by Community Match Score (0–100).
    """
    max_price = BUDGET_PRICE_MAP.get(budget, 1200)

    artisans = db.query(Artisan).filter(Artisan.is_available == True).all()
    experiences = db.query(CommunityExperience).filter(
        CommunityExperience.is_available == True
    ).all()
    exp_map = {e.id: e for e in experiences}

    if not tourist_interests:
        tourist_interests = ["culture", "heritage"]
    tourist_interests_lower = [i.lower() for i in tourist_interests]

    scored = []
    for exp in experiences:
        if exp.price_per_person * group_size > max_price * group_size:
            score_deduction = 15
        else:
            score_deduction = 0

        # Check capacity
        if exp.max_capacity < group_size:
            continue

        # Interest match
        exp_interests = CATEGORY_INTEREST_MAP.get(exp.category, [exp.category])
        matched_interests = set(tourist_interests_lower) & set(exp_interests)
        interest_score = min(len(matched_interests) / max(len(tourist_interests_lower), 1), 1.0) * 50

        # Artisan rating
        artisan = next((a for a in artisans if a.id == exp.artisan_id), None)
        rating_score = ((artisan.rating - 1) / 4.0) * 20 if artisan else 10

        # Community benefit bonus
        community_bonus = 15

        match_score = round(interest_score + rating_score + community_bonus - score_deduction, 1)
        match_score = max(0, min(match_score, 100))

        reasons = []
        if matched_interests:
            reasons.append(f"Matches your interests: {', '.join(matched_interests)}")
        if artisan:
            reasons.append(f"Highly rated artisan ({artisan.rating}/5.0)")
        reasons.append("Supports local Kutch community directly")
        if exp.price_per_person <= 600:
            reasons.append("Budget-friendly experience")

        scored.append({
            "experience_id": exp.id,
            "title": exp.title,
            "category": exp.category,
            "description": exp.description or "",
            "price_per_person": exp.price_per_person,
            "duration_hours": exp.duration_hours,
            "languages": exp.languages,
            "max_capacity": exp.max_capacity,
            "artisan_name": artisan.name if artisan else "Local Artisan",
            "artisan_location": artisan.location if artisan else "",
            "artisan_category": artisan.category if artisan else "",
            "artisan_rating": artisan.rating if artisan else None,
            "latitude": artisan.latitude if artisan else None,
            "longitude": artisan.longitude if artisan else None,
            "match_score": match_score,
            "match_reasons": reasons,
            "data_label": "AI",
        })

    scored.sort(key=lambda x: x["match_score"], reverse=True)
    top = scored[:max_results]

    return {
        "data_label": "AI",
        "matched_experiences": top,
        "total_found": len(scored),
        "parameters": {
            "interests": tourist_interests,
            "budget": budget,
            "group_size": group_size,
        },
        "message": (
            f"Found {len(top)} community experiences matching your interests and budget. "
            "Supporting local artisans directly contributes to Kutch community livelihoods."
        ),
    }


def get_community_overview(db: Session) -> dict:
    """Summary of community tourism assets for authority dashboard."""
    artisans = db.query(Artisan).all()
    experiences = db.query(CommunityExperience).all()
    bookings_count = 0  # Would aggregate from bookings table

    categories = {}
    for a in artisans:
        categories[a.category] = categories.get(a.category, 0) + 1

    return {
        "data_label": "DEMO",
        "total_artisans": len(artisans),
        "active_artisans": sum(1 for a in artisans if a.is_available),
        "total_experiences": len(experiences),
        "artisan_categories": categories,
    }
