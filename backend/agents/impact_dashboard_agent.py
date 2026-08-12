"""
AGENT 5 — Tourism Impact Dashboard Agent

Generates AI-powered analytics summaries for tourism authorities.
DATA LABEL: PREDICTED / AI — all numbers are model estimates.
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models.models import (
    Destination, TouristLoad, EcologicalMetric, CarryingCapacity,
    Alert, AlertSeverity, DestinationStatus
)
from agents.carrying_capacity_agent import calculate_for_destination, get_all_carrying_capacities
from agents.load_forecasting_agent import get_all_forecasts


def get_dashboard_data(db: Session) -> dict:
    """
    Aggregate all dashboard metrics for the authority view.
    """
    destinations = db.query(Destination).filter(Destination.is_active == True).all()
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday = today - timedelta(days=1)

    # Yesterday's actual loads
    yesterday_loads = (
        db.query(TouristLoad)
        .filter(TouristLoad.date == yesterday)
        .all()
    )
    load_map = {tl.destination_id: tl for tl in yesterday_loads}

    # All carrying capacities
    cc_results = get_all_carrying_capacities(db)
    cc_map = {r["destination_id"]: r for r in cc_results}

    # Forecast for tomorrow
    forecasts = get_all_forecasts(db)
    forecast_map = {f["destination_id"]: f for f in forecasts if "destination_id" in f}

    # Build destination summaries
    dest_summaries = []
    total_visitors_yesterday = 0
    overloaded_count = 0
    critical_count = 0
    total_capacity = 0

    for d in destinations:
        load = load_map.get(d.id)
        cc = cc_map.get(d.id, {})
        fc = forecast_map.get(d.id, {})

        actual = load.actual_visitors if load else d.current_load
        total_visitors_yesterday += actual
        total_capacity += d.estimated_capacity
        pressure = cc.get("pressure_level", "low")
        if pressure in ["high", "critical"]:
            overloaded_count += 1
        if pressure == "critical":
            critical_count += 1

        dest_summaries.append({
            "destination_id": d.id,
            "name": d.name,
            "category": d.category.value,
            "latitude": d.latitude,
            "longitude": d.longitude,
            "actual_yesterday": actual,
            "predicted_tomorrow": fc.get("predicted_visitors", 0),
            "capacity": d.estimated_capacity,
            "utilization_pct": round(actual / max(d.estimated_capacity, 1) * 100, 1),
            "cc_score": cc.get("score", 0),
            "pressure_level": pressure,
            "status": d.current_status.value,
            "color": cc.get("color", "#6b7280"),
            "community_opportunities": d.community_opportunities,
        })

    # Sort by pressure (worst first)
    pressure_order = {"critical": 0, "high": 1, "moderate": 2, "low": 3}
    dest_summaries.sort(key=lambda x: pressure_order.get(x["pressure_level"], 4))

    # Active alerts
    active_alerts = db.query(Alert).filter(Alert.is_active == True).all()

    # 30-day trend
    thirty_days = today - timedelta(days=30)
    trend_loads = (
        db.query(TouristLoad)
        .filter(TouristLoad.date >= thirty_days)
        .order_by(TouristLoad.date)
        .all()
    )
    # Aggregate by date
    trend_by_date = {}
    for tl in trend_loads:
        date_str = tl.date.strftime("%Y-%m-%d")
        trend_by_date[date_str] = trend_by_date.get(date_str, 0) + (tl.actual_visitors or 0)

    trend_data = [
        {"date": k, "visitors": v}
        for k, v in sorted(trend_by_date.items())
    ]

    overall_utilization = round(total_visitors_yesterday / max(total_capacity, 1) * 100, 1)

    return {
        "data_label": "PREDICTED",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "summary": {
            "total_active_destinations": len(destinations),
            "total_visitors_yesterday": total_visitors_yesterday,
            "total_capacity": total_capacity,
            "overall_utilization_pct": overall_utilization,
            "overloaded_destinations": overloaded_count,
            "critical_destinations": critical_count,
            "active_alerts": len(active_alerts),
        },
        "destination_pressures": dest_summaries,
        "active_alerts": [
            {
                "id": a.id,
                "destination_id": a.destination_id,
                "type": a.alert_type,
                "title": a.title,
                "message": a.message,
                "severity": a.severity.value,
            }
            for a in active_alerts
        ],
        "trend_30_days": trend_data,
        "disclaimer": (
            "All visitor counts and pressure scores are model estimates based on demo data. "
            "They do not represent official government statistics."
        ),
    }


def generate_ai_insight(dashboard_data: dict) -> str:
    """
    Generate a natural-language summary of the dashboard for the authority.
    This is passed to IBM Granite for final language generation.
    Returns a structured prompt to feed into Granite.
    """
    s = dashboard_data["summary"]
    overloaded = [
        d for d in dashboard_data["destination_pressures"]
        if d["pressure_level"] in ["high", "critical"]
    ]
    under_visited = [
        d for d in dashboard_data["destination_pressures"]
        if d["utilization_pct"] < 30
    ]

    prompt = f"""
You are an AI tourism management advisor for the Rann of Kutch region.
Based on the following dashboard data (all values are model estimates, not official data):

- Total destinations monitored: {s['total_active_destinations']}
- Estimated visitors yesterday: {s['total_visitors_yesterday']:,}
- Overall utilization: {s['overall_utilization_pct']}%
- Destinations under HIGH/CRITICAL pressure: {s['overloaded_destinations']}
- Active alerts: {s['active_alerts']}

High/Critical pressure destinations: {', '.join(d['name'] for d in overloaded[:3])}
Under-visited destinations (< 30% capacity): {', '.join(d['name'] for d in under_visited[:3])}

Write a concise 3-paragraph authority briefing that:
1. Summarizes current tourism pressure situation
2. Highlights top risks needing immediate attention
3. Recommends specific visitor redistribution actions

Important: Clearly frame all statistics as model estimates. Do not state them as verified facts.
"""
    return prompt.strip()
