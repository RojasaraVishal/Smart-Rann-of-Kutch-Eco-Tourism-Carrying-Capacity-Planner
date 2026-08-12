# API Reference

All endpoints return JSON. All AI/ML outputs include `data_label` indicating data source.

| Label | Meaning |
|-------|---------|
| `DEMO` | Synthetic data for demonstration |
| `PREDICTED` | ML model output |
| `AI` | LLM or agent-generated |
| `VERIFIED` | Official/trusted source |

---

## Authentication

### POST /auth/register
Register a new user.

**Body:**
```json
{ "name": "Priya", "email": "priya@example.com", "password": "pass123", "role": "tourist" }
```
**Response:** `{ access_token, token_type, role, name, user_id }`

### POST /auth/login
Login (OAuth2 form).

**Body (form-encoded):** `username=email&password=pass`
**Response:** `{ access_token, token_type, role, name, user_id }`

### GET /auth/me *(🔒 authenticated)*
Returns current user's profile.
**Response:** `{ id, name, email, role }`

---

## Destinations

### GET /destinations/
List all active destinations. Optional query params: `category`, `status`, `community_only`.

### GET /destinations/{id}
Get single destination details.

---

## Tourist Load

### GET /tourist-load/forecast
Forecast tomorrow's visitor load for all destinations.
**Response:** List of forecast objects with `data_label: PREDICTED`.

### GET /tourist-load/forecast/{destination_id}?days=1
Forecast for specific destination. `days` 1–14.

### POST /tourist-load/train
Train XGBoost model on historical DB data.

---

## Carrying Capacity

### GET /carrying-capacity/
Calculate carrying capacity for all destinations.
**Response:** List with `score` (0–100), `pressure_level`, `recommended_action`. `data_label: PREDICTED`.
**⚠️ Disclaimer included in every response.**

### GET /carrying-capacity/{destination_id}
Capacity for single destination.

### GET /carrying-capacity/{destination_id}/alternatives?max_results=3
Find lower-pressure alternatives. `data_label: AI`.

---

## Itinerary

### POST /itinerary/generate/guest
Generate sustainable itinerary (no auth required).

**Body:**
```json
{
  "start_date": "2025-12-15",
  "duration_days": 3,
  "interests": ["desert", "culture", "handicraft"],
  "budget": "moderate",
  "group_size": 4
}
```

**Response:**
```json
{
  "data_label": "AI",
  "itinerary_id": 1,
  "sustainability_score": 72.5,
  "day_by_day": { "1": [...], "2": [...] },
  "recommended_community_experiences": [...],
  "important_note": "AI-generated estimate..."
}
```

---

## Artisans

### GET /artisans/
List all artisans. Optional query: `?category=Embroidery&max_price=500`.

### GET /artisans/{id}
Single artisan details with all experiences.

### GET /artisans/experiences
List all community experiences.

### POST /artisans/match
Find matching experiences using Community Linkage Agent.

**Body:** `{ "interests": [...], "budget": "moderate", "group_size": 4 }`
**Response:** Experiences sorted by `match_score` (0–100). `data_label: AI`.

---

## AI Chat

### POST /ai/chat *(public)*
Conversational eco-assistant.

**Body:**
```json
{ "query": "Plan a 3-day eco trip", "language": "en", "session_id": "optional" }
```

**Response:**
```json
{
  "intent": "plan_trip",
  "agent_results": { ... },
  "granite_response": { "text": "...", "source": "ibm_granite" | "demo_fallback" },
  "data_label": "AI"
}
```

### POST /ai/chat/auth *(🔒 authenticated)*
Same as above but saves conversation history for logged-in users.

---

## Dashboard

### GET /dashboard/tourism-impact *(🔒 authority/admin)*
Full authority dashboard data: summary KPIs, 30-day trends, destination pressures.

### GET /dashboard/tourism-impact/public *(public)*
Public-safe summary (no sensitive per-destination metrics).

### GET /dashboard/tourism-impact/ai-summary *(🔒 authority/admin)*
IBM Granite-powered authority natural-language briefing.

---

## Alerts

### GET /alerts/?active_only=true *(public)*
List active alerts with severity.

### POST /alerts/ *(🔒 authority/admin)*
Create a new alert.

**Body:**
```json
{
  "destination_id": 1,
  "alert_type": "overcrowding",
  "title": "High pressure warning",
  "message": "...",
  "severity": "warning"
}
```

### PATCH /alerts/{id}/deactivate *(🔒 authority/admin)*
Deactivate an alert by ID.
