"""Alerts router — read public alerts + create/manage (authority only)."""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from database import get_db
from models.models import Alert, AlertSeverity
from utils.auth import require_role

router = APIRouter()


def _fmt(a: Alert) -> dict:
    return {
        "id": a.id,
        "destination_id": a.destination_id,
        "type": a.alert_type,
        "title": a.title,
        "message": a.message,
        "severity": a.severity.value,
        "is_active": a.is_active,
        "created_at": a.created_at.isoformat() if a.created_at else None,
        "expires_at": a.expires_at.isoformat() if a.expires_at else None,
    }


@router.get("/")
def list_alerts(
    active_only: bool = Query(True),
    severity: Optional[str] = Query(None, description="info | warning | critical"),
    db: Session = Depends(get_db),
):
    """Public endpoint — list active alerts."""
    q = db.query(Alert)
    if active_only:
        q = q.filter(Alert.is_active == True)
    if severity:
        try:
            q = q.filter(Alert.severity == AlertSeverity(severity))
        except ValueError:
            raise HTTPException(400, f"Invalid severity. Use: info, warning, critical")
    return [_fmt(a) for a in q.order_by(Alert.created_at.desc()).all()]


class AlertCreate(BaseModel):
    destination_id: Optional[int] = None
    alert_type: str
    title: str
    message: str
    severity: str = "info"
    expires_at: Optional[str] = None


@router.post("/", status_code=201)
def create_alert(
    req: AlertCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("authority", "admin")),
):
    """Create a new alert. Requires authority or admin role."""
    try:
        sev = AlertSeverity(req.severity)
    except ValueError:
        raise HTTPException(400, "Invalid severity. Use: info, warning, critical")

    expires = None
    if req.expires_at:
        try:
            expires = datetime.fromisoformat(req.expires_at)
        except ValueError:
            raise HTTPException(400, "expires_at must be ISO format: YYYY-MM-DDTHH:MM:SS")

    alert = Alert(
        destination_id=req.destination_id,
        alert_type=req.alert_type,
        title=req.title,
        message=req.message,
        severity=sev,
        expires_at=expires,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return _fmt(alert)


@router.patch("/{alert_id}/deactivate")
def deactivate_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("authority", "admin")),
):
    """Deactivate an alert. Requires authority or admin role."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(404, "Alert not found")
    alert.is_active = False
    db.commit()
    return {"status": "deactivated", "alert_id": alert_id}
