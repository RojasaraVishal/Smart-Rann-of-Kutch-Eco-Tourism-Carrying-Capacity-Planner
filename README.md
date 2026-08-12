# Smart Rann of Kutch Eco-Tourism & Carrying Capacity Planner

An **Agentic AI** platform powered by **IBM Granite LLM, Machine Learning, and IBM Cloud** that intelligently manages tourist inflow in the Rann of Kutch while protecting fragile ecosystems and supporting local communities.

---

## Quick Start

### Prerequisites
- Python 3.10+
- pip

### 1. Backend Setup

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your IBM Granite API key (optional — demo fallback works without it)
python seed_data.py        # Seed demo destinations, artisans, load history
uvicorn main:app --reload --port 8000
```

> **Note:** Password hashing uses `bcrypt` directly (compatible with bcrypt ≥ 4.x).
> If you upgrade/downgrade the `bcrypt` package, re-seed the DB:
> ```bash
> rm -f kutch_tourism.db && python seed_data.py
> ```

### 2. Frontend
Open `frontend/index.html` directly in a browser, or serve with:
```bash
cd frontend
python -m http.server 3000
```
Then visit http://localhost:3000

### 3. Run Tests
```bash
# From project root:
python -m pytest tests/ -v
```

---

## Project Structure

```
├── backend/
│   ├── main.py                    # FastAPI entry point
│   ├── database.py                # SQLAlchemy setup
│   ├── config.py                  # Settings & env vars
│   ├── seed_data.py               # Demo data seeder
│   ├── requirements.txt
│   ├── models/                    # SQLAlchemy ORM models
│   │   └── models.py
│   ├── routers/                   # API route handlers
│   │   ├── auth.py
│   │   ├── destinations.py
│   │   ├── tourist_load.py
│   │   ├── carrying_capacity.py
│   │   ├── itinerary.py
│   │   ├── artisans.py
│   │   ├── community.py
│   │   ├── ai_chat.py
│   │   ├── alerts.py
│   │   └── dashboard.py
│   ├── agents/                    # Specialized AI agents
│   │   ├── orchestrator.py
│   │   ├── load_forecasting_agent.py
│   │   ├── itinerary_agent.py
│   │   ├── carrying_capacity_agent.py
│   │   ├── community_linkage_agent.py
│   │   └── impact_dashboard_agent.py
│   ├── ml/                        # ML models
│   │   ├── tourist_load_model.py
│   │   └── carrying_capacity_model.py
│   └── utils/
│       ├── auth.py
│       ├── granite.py             # IBM Granite LLM client
│       └── helpers.py
├── frontend/
│   ├── index.html                 # Landing page (hero, stat bar, features)
│   ├── dashboard.html             # Explore Kutch — destination grid + CC badges
│   ├── map.html                   # Interactive Leaflet map with pressure colours
│   ├── planner.html               # Sustainable trip planner (agentic AI)
│   ├── artisans.html              # Artisan marketplace + AI match engine
│   ├── admin.html                 # Authority dashboard (KPIs, Chart.js, role guard)
│   ├── assistant.html             # IBM Granite AI Eco-Assistant (multilingual)
│   ├── login.html                 # Login / register with demo credentials
│   ├── src/
│   │   └── api.js                 # Central API client (auth helpers, timeouts)
│   └── public/
│       └── styles.css             # Full design system (desert-gold palette)
├── tests/
│   ├── test_auth.py
│   ├── test_destinations.py
│   ├── test_carrying_capacity.py
│   ├── test_itinerary.py
│   └── test_agents.py
└── docs/
    ├── architecture.md
    └── api.md
```

---

## Data Classification

| Label | Meaning |
|-------|---------|
| 🟢 VERIFIED | From official/trusted sources |
| 🟡 DEMO | Synthetic data for demonstration |
| 🔵 PREDICTED | ML model forecast |
| 🤖 AI | LLM-generated recommendation |

---

## Security Notes

- Passwords hashed with `bcrypt` (rounds=12) using the `bcrypt` library directly — no passlib dependency
- JWT tokens with configurable expiry
- Role-based access control: `tourist` | `artisan` | `authority` | `admin`
- Authority endpoints (`/dashboard/tourism-impact`, `/dashboard/tourism-impact/ai-summary`) require `authority` or `admin` role
- Public dashboard summary available at `/dashboard/tourism-impact/public` (no auth required)
- Alert create/deactivate require `authority` or `admin` role
- Never expose `IBM_API_KEY` in frontend code

## IBM Technology

- **IBM Granite LLM** — Conversational assistant, itinerary explanations, authority summaries
- **IBM Cloud** — Deployment target

## Demo Credentials

| Role | Email | Password |
|------|-------|----------|
| Tourist | tourist@example.com | password123 |
| Authority | authority@example.com | password123 |
| Admin | admin@kutchtourism.in | password123 |

---

## Core Innovation

> Instead of sending every tourist to the same popular destination, our Agentic AI platform intelligently distributes tourism based on predicted tourist load, ecological carrying capacity, sustainability, and local community opportunities.
# Smart-Rann-of-Kutch-Eco-Tourism-Carrying-Capacity-Planner
