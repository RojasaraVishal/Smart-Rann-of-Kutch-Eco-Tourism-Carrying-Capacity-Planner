"""Destinations router."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from database import get_db
from models.models import Destination, DestinationCategory, DestinationStatus

router = APIRouter()


def _format_dest(d: Destination) -> dict:
    return {
        "id": d.id,
        "name": d.name,
        "local_name": d.local_name,
        "location": d.location,
        "latitude": d.latitude,
        "longitude": d.longitude,
        "category": d.category.value,
        "description": d.description,
        "popularity_score": d.popularity_score,
        "ecological_sensitivity": d.ecological_sensitivity,
        "estimated_capacity": d.estimated_capacity,
        "current_load": d.current_load,
        "water_pressure": d.water_pressure,
        "waste_pressure": d.waste_pressure,
        "infrastructure_capacity": d.infrastructure_capacity,
        "recommended_duration_hours": d.recommended_duration_hours,
        "best_visiting_months": d.best_visiting_months,
        "community_opportunities": d.community_opportunities,
        "sustainable_practices": d.sustainable_practices,
        "current_status": d.current_status.value,
        "data_label": d.data_label,
    }


@router.get("/")
def list_destinations(
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    community_only: bool = Query(False),
    db: Session = Depends(get_db),
):
    q = db.query(Destination).filter(Destination.is_active == True)
    if category:
        try:
            q = q.filter(Destination.category == DestinationCategory(category))
        except ValueError:
            raise HTTPException(400, f"Invalid category: {category}")
    if status:
        try:
            q = q.filter(Destination.current_status == DestinationStatus(status))
        except ValueError:
            raise HTTPException(400, f"Invalid status: {status}")
    if community_only:
        q = q.filter(Destination.community_opportunities == True)
    return [_format_dest(d) for d in q.all()]


@router.get("/{destination_id}")
def get_destination(destination_id: int, db: Session = Depends(get_db)):
    d = db.query(Destination).filter(
        Destination.id == destination_id, Destination.is_active == True
    ).first()
    if not d:
        raise HTTPException(404, "Destination not found")
    return _format_dest(d)
