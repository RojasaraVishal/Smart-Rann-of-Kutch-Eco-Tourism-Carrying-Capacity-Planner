"""Artisans & Community Experiences router.
Fixed: N+1 query replaced with JOIN-based loading.
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from database import get_db
from models.models import Artisan, CommunityExperience
from agents.community_linkage_agent import match_community_experiences
from pydantic import BaseModel

router = APIRouter()


@router.get("/")
def list_artisans(
    category: Optional[str] = Query(None, description="Filter by craft category"),
    available_only: bool = Query(True),
    db: Session = Depends(get_db),
):
    q = db.query(Artisan)
    if available_only:
        q = q.filter(Artisan.is_available == True)
    if category:
        q = q.filter(Artisan.category.ilike(f"%{category}%"))
    artisans = q.all()
    return [
        {
            "id": a.id,
            "name": a.name,
            "bio": a.bio,
            "location": a.location,
            "latitude": a.latitude,
            "longitude": a.longitude,
            "category": a.category,
            "speciality": a.speciality,
            "rating": a.rating,
            "data_label": a.data_label,
        }
        for a in artisans
    ]


@router.get("/experiences")
def list_experiences(
    category: Optional[str] = Query(None),
    max_price: Optional[float] = Query(None),
    db: Session = Depends(get_db),
):
    """List all community experiences with artisan data in a single JOIN query."""
    # Single query with eager-loaded artisan — avoids N+1
    q = (
        db.query(CommunityExperience)
        .options(joinedload(CommunityExperience.artisan))
        .filter(CommunityExperience.is_available == True)
    )
    if category:
        q = q.filter(CommunityExperience.category.ilike(f"%{category}%"))
    if max_price is not None:
        q = q.filter(CommunityExperience.price_per_person <= max_price)

    experiences = q.all()
    result = []
    for e in experiences:
        a = e.artisan
        result.append({
            "id": e.id,
            "title": e.title,
            "description": e.description,
            "category": e.category,
            "price_per_person": e.price_per_person,
            "max_capacity": e.max_capacity,
            "duration_hours": e.duration_hours,
            "languages": e.languages,
            "artisan_id": a.id if a else None,
            "artisan_name": a.name if a else "Local Artisan",
            "artisan_location": a.location if a else "",
            "artisan_rating": round(a.rating, 1) if a and a.rating else None,
            "artisan_category": a.category if a else "",
            "latitude": a.latitude if a else None,
            "longitude": a.longitude if a else None,
            "data_label": e.data_label,
        })
    return result


@router.get("/{artisan_id}")
def get_artisan(artisan_id: int, db: Session = Depends(get_db)):
    """Get a single artisan with their experiences."""
    a = db.query(Artisan).filter(Artisan.id == artisan_id).first()
    if not a:
        raise HTTPException(404, "Artisan not found")
    experiences = (
        db.query(CommunityExperience)
        .filter(CommunityExperience.artisan_id == artisan_id,
                CommunityExperience.is_available == True)
        .all()
    )
    return {
        "id": a.id,
        "name": a.name,
        "bio": a.bio,
        "location": a.location,
        "latitude": a.latitude,
        "longitude": a.longitude,
        "category": a.category,
        "speciality": a.speciality,
        "rating": a.rating,
        "data_label": a.data_label,
        "experiences": [
            {
                "id": e.id,
                "title": e.title,
                "description": e.description,
                "category": e.category,
                "price_per_person": e.price_per_person,
                "max_capacity": e.max_capacity,
                "duration_hours": e.duration_hours,
                "languages": e.languages,
            }
            for e in experiences
        ],
    }


class CommunityMatchRequest(BaseModel):
    interests: List[str] = ["culture", "handicraft"]
    budget: str = "moderate"
    group_size: int = 2


@router.post("/match")
def match_community(req: CommunityMatchRequest, db: Session = Depends(get_db)):
    return match_community_experiences(
        db, req.interests, req.budget, req.group_size
    )
