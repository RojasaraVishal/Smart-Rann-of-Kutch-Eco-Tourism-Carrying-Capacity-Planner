"""Carrying Capacity router."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from agents import carrying_capacity_agent as cca

router = APIRouter()


@router.get("/")
def all_carrying_capacities(db: Session = Depends(get_db)):
    """Calculate and return carrying capacity for all active destinations."""
    return cca.get_all_carrying_capacities(db)


@router.get("/{destination_id}")
def destination_carrying_capacity(destination_id: int, db: Session = Depends(get_db)):
    return cca.calculate_for_destination(db, destination_id)


@router.get("/{destination_id}/alternatives")
def destination_alternatives(
    destination_id: int,
    max_results: int = Query(3, ge=1, le=6),
    db: Session = Depends(get_db),
):
    """Find alternative destinations when a destination is overloaded."""
    return cca.find_alternatives(db, destination_id, max_results)
