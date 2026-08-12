# Architecture

## System Overview

```
Tourist / Authority / Artisan
         ↓
  Web Application (HTML/JS)
         ↓
  FastAPI Backend (Python)
         ↓
  AI Orchestrator (agents/orchestrator.py)
         ↓
  ┌──────────────────────────────────────────┐
  │  Specialized AI Agents                    │
  │  ├── Load Forecasting Agent (Agent 1)    │
  │  ├── Itinerary Agent (Agent 2)           │
  │  ├── Carrying Capacity Agent (Agent 3)  │
  │  ├── Community Linkage Agent (Agent 4)  │
  │  └── Impact Dashboard Agent (Agent 5)  │
  └──────────────────────────────────────────┘
         ↓
  ML Models + Database (SQLite/PostgreSQL)
         ↓
  IBM Granite LLM (watsonx.ai)
         ↓
  Personalized Response
```

## Agent Architecture

| Agent | File | Purpose | Output Label |
|-------|------|---------|-------------|
| Orchestrator | `agents/orchestrator.py` | Intent detection + routing | AI |
| Load Forecasting | `agents/load_forecasting_agent.py` | Predict visitor counts | PREDICTED |
| Itinerary | `agents/itinerary_agent.py` | Generate sustainable trips | AI |
| Carrying Capacity | `agents/carrying_capacity_agent.py` | Pressure score + alternatives | PREDICTED |
| Community Linkage | `agents/community_linkage_agent.py` | Artisan/experience matching | AI |
| Impact Dashboard | `agents/impact_dashboard_agent.py` | Authority analytics + briefing | PREDICTED/AI |

## Data Flow

1. Tourist submits query via frontend
2. `POST /ai/chat` receives it
3. Orchestrator detects intent
4. Relevant agents are called:
   - Load Forecasting Agent reads `tourist_load` history + ML model
   - Carrying Capacity Agent reads `ecological_metrics` + formula
   - Itinerary Agent combines above + community matching
5. IBM Granite LLM generates natural-language explanation
6. Response returned with `data_label` on every field

## Carrying Capacity Formula

```
Score = 100 × (
    0.30 × tourist_load_ratio +
    0.20 × water_stress +
    0.15 × waste_stress +
    0.15 × infrastructure_stress +
    0.20 × ecological_risk_normalized
)
```

Weights are configurable in `backend/config.py` via environment variables.

⚠️ This score is a **model estimate for planning purposes only**. It is NOT an official ecological limit.

## IBM Granite Integration

File: `backend/utils/granite.py`

- Uses IBM watsonx.ai Inference API
- Authenticates via IAM token exchange
- Falls back gracefully to demo message if `IBM_API_KEY` not set
- Never exposes credentials in responses

## Security

- JWT authentication (HS256)
- bcrypt password hashing
- Role-based access control (`require_role()` dependency)
- SQL injection protection via SQLAlchemy ORM
- Input validation via Pydantic
- Environment variables for all secrets
- Rate limiting via slowapi
- CORS configured (restrict origins in production)
