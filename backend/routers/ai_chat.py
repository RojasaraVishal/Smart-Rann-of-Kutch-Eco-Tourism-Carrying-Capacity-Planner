"""AI Chat router — Tourist Eco-Assistant powered by IBM Granite."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database import get_db
from agents.orchestrator import orchestrate
from models.models import AIInteraction
from utils.auth import get_current_user

router = APIRouter()


class ChatRequest(BaseModel):
    query: str
    language: str = "en"   # en, hi, gu
    session_id: Optional[str] = None


@router.post("/chat")
async def chat(req: ChatRequest, db: Session = Depends(get_db)):
    """
    Public AI chat endpoint (no auth required for accessibility).
    """
    result = await orchestrate(db, req.query, tourist_id=None, language=req.language)
    # Persist interaction
    interaction = AIInteraction(
        agent=result.get("intent", "orchestrator"),
        query=req.query,
        response=result.get("granite_response", {}).get("text", ""),
        language=req.language,
        session_id=req.session_id,
    )
    db.add(interaction)
    db.commit()
    return result


@router.post("/chat/auth")
async def chat_authenticated(
    req: ChatRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Authenticated chat — uses tourist profile for personalization."""
    from models.models import TouristProfile
    profile = db.query(TouristProfile).filter(TouristProfile.user_id == current_user.id).first()
    tourist_id = profile.id if profile else None
    result = await orchestrate(db, req.query, tourist_id=tourist_id, language=req.language)
    interaction = AIInteraction(
        user_id=current_user.id,
        agent=result.get("intent", "orchestrator"),
        query=req.query,
        response=result.get("granite_response", {}).get("text", ""),
        language=req.language,
        session_id=req.session_id,
    )
    db.add(interaction)
    db.commit()
    return result
