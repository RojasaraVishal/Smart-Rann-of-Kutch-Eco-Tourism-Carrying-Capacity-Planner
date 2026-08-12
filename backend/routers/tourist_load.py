"""Tourist Load router."""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
from database import get_db
from agents import load_forecasting_agent as lfa

router = APIRouter()


@router.get("/forecast")
def forecast_all(db: Session = Depends(get_db)):
    """Forecast tomorrow's tourist load for all destinations."""
    return lfa.get_all_forecasts(db)


@router.get("/forecast/{destination_id}")
def forecast_destination(
    destination_id: int,
    days: int = Query(1, ge=1, le=14),
    date: Optional[str] = Query(None, description="YYYY-MM-DD, defaults to tomorrow"),
    db: Session = Depends(get_db),
):
    target = None
    if date:
        try:
            target = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(400, "Date must be YYYY-MM-DD")
    return lfa.forecast_destination(db, destination_id, target, days)


@router.post("/train")
def train_model(db: Session = Depends(get_db)):
    """Train the XGBoost tourist load model on historical DB data."""
    return lfa.train_model_from_db(db)


@router.get("/history/{destination_id}")
def load_history(
    destination_id: int,
    days: int = Query(30, ge=1, le=90),
    db: Session = Depends(get_db),
):
    from models.models import TouristLoad
    cutoff = datetime.utcnow() - timedelta(days=days)
    records = (
        db.query(TouristLoad)
        .filter(
            TouristLoad.destination_id == destination_id,
            TouristLoad.date >= cutoff,
        )
        .order_by(TouristLoad.date)
        .all()
    )
    return [
        {
            "date": r.date.strftime("%Y-%m-%d"),
            "actual_visitors": r.actual_visitors,
            "predicted_visitors": r.predicted_visitors,
            "day_of_week": r.day_of_week,
            "is_event_period": r.is_event_period,
            "confidence_score": r.confidence_score,
            "data_label": r.data_label,
        }
        for r in records
    ]
