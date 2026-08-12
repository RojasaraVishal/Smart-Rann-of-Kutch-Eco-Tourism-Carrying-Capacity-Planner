"""Itinerary router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from database import get_db
from agents.itinerary_agent import generate_itinerary
from utils.auth import get_current_user

router = APIRouter()


class ItineraryRequest(BaseModel):
    start_date: str           # YYYY-MM-DD
    duration_days: int = 3
    interests: List[str] = ["desert", "culture", "heritage"]
    budget: str = "moderate"
    group_size: int = 2


@router.post("/generate")
def generate(
    req: ItineraryRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        start = datetime.strptime(req.start_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(400, "start_date must be YYYY-MM-DD")

    from models.models import TouristProfile
    profile = db.query(TouristProfile).filter(TouristProfile.user_id == current_user.id).first()
    tourist_profile_id = profile.id if profile else 1

    return generate_itinerary(
        db,
        tourist_profile_id=tourist_profile_id,
        start_date=start,
        duration_days=req.duration_days,
        interests=req.interests,
        budget=req.budget,
        group_size=req.group_size,
    )


@router.post("/generate/guest")
def generate_guest(req: ItineraryRequest, db: Session = Depends(get_db)):
    """Generate itinerary without authentication (for demo/public access)."""
    try:
        start = datetime.strptime(req.start_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(400, "start_date must be YYYY-MM-DD")

    return generate_itinerary(
        db,
        tourist_profile_id=1,
        start_date=start,
        duration_days=req.duration_days,
        interests=req.interests,
        budget=req.budget,
        group_size=req.group_size,
    )
