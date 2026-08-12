"""
AGENT 1 — Tourist Load Forecasting Agent

Predicts tourist inflow for destinations and time periods.
DATA LABEL: PREDICTED — never present as guaranteed or official.
"""
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from models.models import Destination, TouristLoad
from ml.tourist_load_model import TouristLoadForecaster
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


_forecaster = TouristLoadForecaster()


def train_model_from_db(db: Session) -> dict:
    """Pull historical data from DB and train the XGBoost model."""
    loads = db.query(TouristLoad).all()
    destinations = {d.id: d for d in db.query(Destination).all()}

    if not loads:
        return {"status": "no_data", "detail": "No tourist load history found in database."}

    rows = []
    for tl in loads:
        dest = destinations.get(tl.destination_id)
        if not dest:
            continue
        rows.append({
            "date": tl.date,
            "destination_id": tl.destination_id,
            "actual_visitors": tl.actual_visitors,
            "day_of_week": tl.day_of_week or tl.date.weekday(),
            "is_holiday": int(tl.is_holiday or 0),
            "is_event_period": int(tl.is_event_period or 0),
            "popularity_score": dest.popularity_score,
            "estimated_capacity": dest.estimated_capacity,
        })

    df = pd.DataFrame(rows)
    result = _forecaster.train(df)
    return result


def forecast_destination(
    db: Session,
    destination_id: int,
    target_date: Optional[datetime] = None,
    days: int = 1,
) -> dict:
    """
    Forecast tourist load for a destination.

    Args:
        destination_id: DB id of destination
        target_date: start date (defaults to tomorrow)
        days: number of days to forecast (1–14)
    Returns:
        Forecast dict with data_label = PREDICTED
    """
    dest = db.query(Destination).filter(Destination.id == destination_id).first()
    if not dest:
        return {"error": f"Destination {destination_id} not found"}

    if target_date is None:
        target_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)

    is_event = dest.name in ["White Rann, Dhordo", "Rann Utsav Tent City"] and target_date.month in [11, 12, 1, 2]
    days = max(1, min(days, 14))

    if days == 1:
        forecast = _forecaster.predict(
            target_date, dest.popularity_score, dest.estimated_capacity, is_event
        )
    else:
        forecast = {
            "data_label": "PREDICTED",
            "destination": dest.name,
            "days": _forecaster.forecast_week(target_date, dest.popularity_score, dest.estimated_capacity, is_event)[:days],
            "note": "All values are model estimates."
        }
        return {**forecast, "destination_id": dest.id, "destination_name": dest.name}

    return {
        **forecast,
        "destination_id": dest.id,
        "destination_name": dest.name,
        "category": dest.category.value,
    }


def get_all_forecasts(db: Session, target_date: Optional[datetime] = None) -> list:
    """Return tomorrow's forecast for every destination."""
    if target_date is None:
        target_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    destinations = db.query(Destination).filter(Destination.is_active == True).all()
    return [
        forecast_destination(db, d.id, target_date)
        for d in destinations
    ]
