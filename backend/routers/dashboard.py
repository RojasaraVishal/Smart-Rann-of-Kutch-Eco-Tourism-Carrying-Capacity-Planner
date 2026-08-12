"""Dashboard router — Tourism Impact Dashboard for authorities.
Requires authority or admin role.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from agents.impact_dashboard_agent import get_dashboard_data, generate_ai_insight
from utils.granite import call_granite
from utils.auth import require_role

router = APIRouter()


@router.get("/tourism-impact")
def tourism_impact(
    db: Session = Depends(get_db),
    current_user=Depends(require_role("authority", "admin")),
):
    """Full tourism impact dashboard data. Requires authority or admin role."""
    return get_dashboard_data(db)


@router.get("/tourism-impact/public")
def tourism_impact_public(db: Session = Depends(get_db)):
    """Reduced public dashboard — safe summary without sensitive authority data."""
    data = get_dashboard_data(db)
    return {
        "data_label": data["data_label"],
        "generated_at": data["generated_at"],
        "summary": {
            "total_active_destinations": data["summary"]["total_active_destinations"],
            "overloaded_destinations": data["summary"]["overloaded_destinations"],
            "active_alerts": data["summary"]["active_alerts"],
        },
        "active_alerts": data["active_alerts"],
        "disclaimer": data["disclaimer"],
    }


@router.get("/tourism-impact/ai-summary")
async def tourism_impact_ai_summary(
    db: Session = Depends(get_db),
    current_user=Depends(require_role("authority", "admin")),
):
    """AI-generated authority briefing using IBM Granite. Requires authority or admin role."""
    dashboard = get_dashboard_data(db)
    prompt = generate_ai_insight(dashboard)
    try:
        granite = await call_granite(prompt, max_new_tokens=500, temperature=0.3)
    except Exception as e:
        granite = {
            "text": "AI briefing unavailable. Check IBM Granite configuration.",
            "source": "error_fallback",
            "data_label": "AI",
        }
    return {
        "data_label": "AI",
        "summary": granite,
        "dashboard_data": dashboard,
    }
