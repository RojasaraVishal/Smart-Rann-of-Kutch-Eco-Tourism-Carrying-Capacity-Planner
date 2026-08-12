"""General helper utilities."""
from datetime import datetime


def utcnow_str() -> str:
    return datetime.utcnow().isoformat() + "Z"


def clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def load_label_from_pct(pct: float) -> str:
    if pct < 40:
        return "LOW"
    elif pct < 65:
        return "MODERATE"
    elif pct < 85:
        return "HIGH"
    return "CRITICAL"


def pressure_color(level: str) -> str:
    return {
        "low": "#22c55e",
        "moderate": "#f59e0b",
        "high": "#f97316",
        "critical": "#ef4444",
    }.get(level, "#6b7280")
