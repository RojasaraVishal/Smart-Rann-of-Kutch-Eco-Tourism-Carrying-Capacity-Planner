"""
AI Orchestrator — routes tourist/authority queries to the right agents.

Architecture:
  User Query → Orchestrator → Identify intent → Call agents → Synthesize → Granite → Response

Supported intents:
  - plan_trip
  - check_crowd
  - find_alternatives
  - match_community
  - carrying_capacity
  - dashboard_insight
  - general_chat
"""
import re
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from utils.granite import call_granite

# Intent keyword patterns
INTENT_PATTERNS = {
    "plan_trip": [
        r"plan.*trip", r"itinerary", r"3.day", r"5.day", r"day.*trip",
        r"eke.*plan", r"eco.*trip", r"sustainable.*travel", r"tour.*plan",
        r"trip.*kutch", r"visit.*kutch",
    ],
    "check_crowd": [
        r"crowd", r"busy", r"how many.*tourist", r"tourist.*load",
        r"congested", r"overcrowd", r"peak.*time", r"less.*crowd",
        r"avoid.*crowd", r"quiet",
    ],
    "find_alternatives": [
        r"alternative", r"other.*place", r"instead.*of", r"similar.*to",
        r"less.*popular", r"hidden.*gem", r"lesser.*known",
    ],
    "match_community": [
        r"artisan", r"craft", r"handicraft", r"local.*experience",
        r"community", r"homestay", r"workshop", r"embroidery", r"weaving",
        r"local.*culture", r"folk",
    ],
    "carrying_capacity": [
        r"capacity", r"can i visit", r"safe to visit", r"restriction",
        r"permit", r"is.*open", r"ecological",
    ],
}

SYSTEM_PROMPT = """You are the Smart Rann of Kutch Eco-Tourism AI Assistant.
You help tourists plan sustainable trips to the Kutch region of Gujarat, India.
You speak English, Hindi, and Gujarati.
Always be helpful, accurate, and eco-conscious.
When recommending destinations, prioritize sustainability and local community benefit.
Never fabricate visitor counts, government restrictions, prices, or availability — always state when information is unavailable.
Clearly distinguish between verified data, model estimates, and AI recommendations.
"""


def detect_intent(query: str) -> str:
    query_lower = query.lower()
    for intent, patterns in INTENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, query_lower):
                return intent
    return "general_chat"


async def orchestrate(
    db: Session,
    query: str,
    tourist_id: Optional[int] = None,
    language: str = "en",
) -> dict:
    """
    Main orchestration entry point.

    Returns:
    {
      intent: str,
      agent_results: dict,   # Raw agent outputs
      granite_response: dict, # LLM-generated text
      data_label: "AI"
    }
    """
    intent = detect_intent(query)
    agent_results = {}

    # ── AGENT ROUTING ────────────────────────────────────────────────────────

    if intent == "plan_trip":
        from agents.itinerary_agent import generate_itinerary
        from models.models import TouristProfile
        # Extract duration (look for numbers)
        duration = 3  # default
        m = re.search(r"(\d+)\s*day", query.lower())
        if m:
            duration = int(m.group(1))
        # Default interests from profile or query keywords
        interests = _extract_interests(query)
        profile = db.query(TouristProfile).filter(TouristProfile.id == tourist_id).first() if tourist_id else None
        if profile and profile.interests:
            interests = interests or profile.interests
        if not interests:
            interests = ["desert", "culture", "heritage"]
        budget = _extract_budget(query)
        group = _extract_group_size(query)
        itin = generate_itinerary(
            db,
            tourist_profile_id=tourist_id or 1,
            start_date=datetime.utcnow(),
            duration_days=duration,
            interests=interests,
            budget=budget,
            group_size=group,
        )
        agent_results = {"itinerary": itin}
        prompt = _build_itinerary_prompt(query, itin, language)

    elif intent == "check_crowd":
        from agents.load_forecasting_agent import get_all_forecasts
        forecasts = get_all_forecasts(db)
        agent_results = {"forecasts": forecasts[:8]}
        prompt = _build_crowd_prompt(query, forecasts[:8], language)

    elif intent == "find_alternatives":
        from agents.carrying_capacity_agent import get_all_carrying_capacities
        cc_all = get_all_carrying_capacities(db)
        high_pressure = [r for r in cc_all if r.get("pressure_level") in ["high", "critical"]]
        agent_results = {"high_pressure": high_pressure, "all_cc": cc_all[:6]}
        prompt = _build_alternatives_prompt(query, cc_all, language)

    elif intent == "match_community":
        from agents.community_linkage_agent import match_community_experiences
        interests = _extract_interests(query) or ["culture", "handicraft"]
        budget = _extract_budget(query)
        community = match_community_experiences(db, interests, budget)
        agent_results = {"community": community}
        prompt = _build_community_prompt(query, community, language)

    elif intent == "carrying_capacity":
        from agents.carrying_capacity_agent import get_all_carrying_capacities
        cc_all = get_all_carrying_capacities(db)
        agent_results = {"carrying_capacities": cc_all}
        prompt = _build_capacity_prompt(query, cc_all, language)

    elif intent == "dashboard_insight":
        from agents.impact_dashboard_agent import get_dashboard_data, generate_ai_insight
        dashboard = get_dashboard_data(db)
        prompt = generate_ai_insight(dashboard)
        agent_results = {"dashboard": dashboard}

    else:
        # General eco-tourism chat
        prompt = f"{SYSTEM_PROMPT}\n\nUser ({language}): {query}\n\nAssistant:"

    # ── IBM GRANITE ──────────────────────────────────────────────────────────
    granite_resp = await call_granite(prompt, system_prompt=SYSTEM_PROMPT)

    return {
        "data_label": "AI",
        "intent": intent,
        "language": language,
        "agent_results": agent_results,
        "granite_response": granite_resp,
        "query": query,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


# ── Prompt Builders ──────────────────────────────────────────────────────────

def _build_itinerary_prompt(query: str, itin: dict, lang: str) -> str:
    days = itin.get("day_by_day", {})
    day_text = ""
    for day_num, stops in days.items():
        day_text += f"\nDay {day_num}:\n"
        for s in stops:
            day_text += (
                f"  - {s['time_slot'].capitalize()}: {s['destination_name']} "
                f"({s['category']}, crowd: {s['crowd_level']}, "
                f"CC score: {s['carrying_capacity_score']:.0f}/100)\n"
                f"    Reason: {s['reason']}\n"
            )
    sus_score = itin.get("sustainability_score", 0)
    return (
        f"The tourist asked: '{query}'\n\n"
        f"Our AI has generated this {itin.get('duration_days', 3)}-day itinerary:\n"
        f"{day_text}\n"
        f"Sustainability Score: {sus_score}/100 ({itin.get('sustainability_label', '')})\n\n"
        f"Please explain this itinerary to the tourist in a friendly, helpful way. "
        f"Mention why each destination was chosen (crowd levels, sustainability, community). "
        f"Include practical travel advice. Language: {lang}. "
        f"Note that all carrying capacity scores are model estimates, not official data."
    )


def _build_crowd_prompt(query: str, forecasts: list, lang: str) -> str:
    forecast_text = "\n".join(
        f"- {f.get('destination_name', 'Unknown')}: {f.get('load_label', 'N/A')} "
        f"(estimated {f.get('predicted_visitors', '?')} visitors, {f.get('utilization_pct', 0)}% capacity)"
        for f in forecasts if "destination_name" in f
    )
    return (
        f"Tourist asked: '{query}'\n\n"
        f"Tomorrow's predicted tourist loads (all estimates, not official data):\n{forecast_text}\n\n"
        f"Identify the least crowded destinations and explain which places are best to visit "
        f"for a comfortable, uncrowded experience. Language: {lang}."
    )


def _build_alternatives_prompt(query: str, cc_all: list, lang: str) -> str:
    low_pressure = [c for c in cc_all if c.get("pressure_level") in ["low", "moderate"]][:5]
    alt_text = "\n".join(
        f"- {c.get('destination_name', '?')}: CC score {c.get('score', 0):.0f}/100 ({c.get('pressure_level', '')})"
        for c in low_pressure
    )
    return (
        f"Tourist asked: '{query}'\n\n"
        f"Destinations with lower tourism pressure (model estimates):\n{alt_text}\n\n"
        f"Recommend the best alternatives with brief explanations of what makes them special. "
        f"Language: {lang}."
    )


def _build_community_prompt(query: str, community: dict, lang: str) -> str:
    exps = community.get("matched_experiences", [])[:3]
    exp_text = "\n".join(
        f"- {e['title']} by {e['artisan_name']} (match: {e['match_score']}%, ₹{e['price_per_person']}/person)"
        for e in exps
    )
    return (
        f"Tourist asked: '{query}'\n\n"
        f"Top community experiences matched:\n{exp_text}\n\n"
        f"Describe these experiences warmly, explain why they support local communities, "
        f"and encourage the tourist to participate. Language: {lang}."
    )


def _build_capacity_prompt(query: str, cc_all: list, lang: str) -> str:
    cc_text = "\n".join(
        f"- {c.get('destination_name', '?')}: {c.get('score', 0):.0f}/100 ({c.get('pressure_level', '')}) — {c.get('recommended_action', '')}"
        for c in cc_all[:6]
    )
    return (
        f"Tourist asked: '{query}'\n\n"
        f"Carrying capacity status (model estimates, not official ecological limits):\n{cc_text}\n\n"
        f"Answer the tourist's question about visiting capacity/restrictions honestly, "
        f"clearly noting these are estimates and they should check official sources for permit requirements. "
        f"Language: {lang}."
    )


# ── Helpers ──────────────────────────────────────────────────────────────────

def _extract_interests(query: str) -> list:
    interest_keywords = {
        "desert": ["desert", "rann", "white rann", "sand"],
        "wildlife": ["wildlife", "bird", "flamingo", "wild ass", "animal"],
        "culture": ["culture", "festival", "music", "dance", "utsav"],
        "heritage": ["heritage", "fort", "palace", "history", "temple"],
        "handicraft": ["handicraft", "craft", "embroidery", "weaving", "ajrakh", "bandhani"],
        "village": ["village", "rural", "community"],
        "photography": ["photo", "photography", "sunrise", "sunset"],
        "nature": ["nature", "scenic", "landscape"],
        "adventure": ["adventure", "trek", "jeep", "off-road"],
    }
    found = []
    q = query.lower()
    for interest, keywords in interest_keywords.items():
        if any(kw in q for kw in keywords):
            found.append(interest)
    return found


def _extract_budget(query: str) -> str:
    q = query.lower()
    if any(w in q for w in ["budget", "cheap", "affordable", "low cost"]):
        return "budget"
    if any(w in q for w in ["luxury", "premium", "5 star", "expensive"]):
        return "luxury"
    return "moderate"


def _extract_group_size(query: str) -> int:
    m = re.search(r"(family of|group of|(\d+)\s*people|(\d+)\s*person)", query.lower())
    if m:
        nums = re.findall(r"\d+", m.group(0))
        if nums:
            return int(nums[0])
    if "family" in query.lower():
        return 4
    return 2
