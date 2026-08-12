"""
SQLAlchemy ORM models — full normalized schema.

Tables:
  users, tourists, destinations, tourist_load, ecological_metrics,
  carrying_capacity, itineraries, itinerary_destinations,
  artisans, community_experiences, bookings, alerts, ai_interactions
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime,
    Text, ForeignKey, Enum, Index, JSON
)
from sqlalchemy.orm import relationship
import enum
from database import Base


# ─── Enums ──────────────────────────────────────────────────────────────────

class UserRole(str, enum.Enum):
    tourist = "tourist"
    authority = "authority"
    artisan = "artisan"
    operator = "operator"
    admin = "admin"


class DestinationCategory(str, enum.Enum):
    desert = "desert"
    wildlife = "wildlife"
    culture = "culture"
    heritage = "heritage"
    village = "village"
    handicraft = "handicraft"
    nature = "nature"
    adventure = "adventure"
    photography = "photography"
    community = "community"


class PressureLevel(str, enum.Enum):
    low = "low"
    moderate = "moderate"
    high = "high"
    critical = "critical"


class DestinationStatus(str, enum.Enum):
    open = "open"
    normal = "normal"
    encourage_alternatives = "encourage_alternatives"
    restricted = "restricted"
    temporarily_closed = "temporarily_closed"
    permit_required = "permit_required"


class AlertSeverity(str, enum.Enum):
    info = "info"
    warning = "warning"
    critical = "critical"


class BookingStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"


# ─── Users ──────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.tourist)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    tourist_profile = relationship("TouristProfile", back_populates="user", uselist=False)
    ai_interactions = relationship("AIInteraction", back_populates="user")
    bookings = relationship("Booking", back_populates="tourist")


class TouristProfile(Base):
    __tablename__ = "tourists"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    preferences = Column(JSON, default=dict)      # {interests, activities, etc.}
    budget = Column(String(50))                    # "budget", "moderate", "luxury"
    interests = Column(JSON, default=list)         # ["desert", "culture", ...]
    group_size = Column(Integer, default=1)
    mobility_preference = Column(String(50))

    user = relationship("User", back_populates="tourist_profile")
    itineraries = relationship("Itinerary", back_populates="tourist")


# ─── Destinations ────────────────────────────────────────────────────────────

class Destination(Base):
    __tablename__ = "destinations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    local_name = Column(String(150))              # Gujarati/Hindi name
    location = Column(String(200))
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    category = Column(Enum(DestinationCategory), nullable=False)
    description = Column(Text)
    popularity_score = Column(Float, default=5.0)  # 1–10
    ecological_sensitivity = Column(Float, default=5.0)  # 1–10 (10 = most sensitive)
    estimated_capacity = Column(Integer)           # Max daily visitors
    current_load = Column(Integer, default=0)      # Live/recent visitor count
    water_pressure = Column(Float, default=0.5)    # 0–1 normalised
    waste_pressure = Column(Float, default=0.5)
    infrastructure_capacity = Column(Float, default=0.5)  # 1 = full capacity
    recommended_duration_hours = Column(Float, default=2.0)
    best_visiting_months = Column(JSON, default=list)
    community_opportunities = Column(Boolean, default=False)
    sustainable_practices = Column(Text)
    current_status = Column(Enum(DestinationStatus), default=DestinationStatus.open)
    image_url = Column(String(500))
    data_label = Column(String(20), default="DEMO")  # VERIFIED / DEMO
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    tourist_loads = relationship("TouristLoad", back_populates="destination")
    ecological_metrics = relationship("EcologicalMetric", back_populates="destination")
    carrying_capacities = relationship("CarryingCapacity", back_populates="destination")
    alerts = relationship("Alert", back_populates="destination")


# ─── Tourist Load ─────────────────────────────────────────────────────────────

class TouristLoad(Base):
    __tablename__ = "tourist_load"

    id = Column(Integer, primary_key=True, index=True)
    destination_id = Column(Integer, ForeignKey("destinations.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    actual_visitors = Column(Integer)
    predicted_visitors = Column(Integer)
    day_of_week = Column(Integer)                  # 0=Mon … 6=Sun
    is_holiday = Column(Boolean, default=False)
    is_event_period = Column(Boolean, default=False)
    weather_condition = Column(String(50))
    confidence_score = Column(Float)               # ML confidence 0–1
    data_label = Column(String(20), default="DEMO")

    destination = relationship("Destination", back_populates="tourist_loads")

    __table_args__ = (
        Index("ix_load_dest_date", "destination_id", "date"),
    )


# ─── Ecological Metrics ───────────────────────────────────────────────────────

class EcologicalMetric(Base):
    __tablename__ = "ecological_metrics"

    id = Column(Integer, primary_key=True, index=True)
    destination_id = Column(Integer, ForeignKey("destinations.id"), nullable=False)
    date = Column(DateTime, nullable=False, default=datetime.utcnow)
    water_stress = Column(Float, default=0.5)       # 0–1
    waste_stress = Column(Float, default=0.5)
    infrastructure_stress = Column(Float, default=0.5)
    ecological_risk = Column(Float, default=0.5)
    notes = Column(Text)
    data_label = Column(String(20), default="DEMO")

    destination = relationship("Destination", back_populates="ecological_metrics")


# ─── Carrying Capacity ────────────────────────────────────────────────────────

class CarryingCapacity(Base):
    __tablename__ = "carrying_capacity"

    id = Column(Integer, primary_key=True, index=True)
    destination_id = Column(Integer, ForeignKey("destinations.id"), nullable=False)
    score = Column(Float, nullable=False)           # 0–100
    pressure_level = Column(Enum(PressureLevel))
    status = Column(Enum(DestinationStatus))
    tourist_load_pct = Column(Float)
    water_stress = Column(Float)
    waste_stress = Column(Float)
    infrastructure_stress = Column(Float)
    ecological_risk = Column(Float)
    recommended_action = Column(Text)
    calculated_at = Column(DateTime, default=datetime.utcnow)
    data_label = Column(String(20), default="PREDICTED")

    destination = relationship("Destination", back_populates="carrying_capacities")


# ─── Itineraries ──────────────────────────────────────────────────────────────

class Itinerary(Base):
    __tablename__ = "itineraries"

    id = Column(Integer, primary_key=True, index=True)
    tourist_id = Column(Integer, ForeignKey("tourists.id"), nullable=False)
    title = Column(String(200))
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    sustainability_score = Column(Float)            # 0–100
    crowd_score = Column(Float)
    local_benefit_score = Column(Float)
    total_distance_km = Column(Float)
    explanation = Column(Text)                      # LLM-generated
    data_label = Column(String(20), default="AI")
    created_at = Column(DateTime, default=datetime.utcnow)

    tourist = relationship("TouristProfile", back_populates="itineraries")
    stops = relationship("ItineraryDestination", back_populates="itinerary",
                         order_by="ItineraryDestination.day_number")


class ItineraryDestination(Base):
    __tablename__ = "itinerary_destinations"

    id = Column(Integer, primary_key=True, index=True)
    itinerary_id = Column(Integer, ForeignKey("itineraries.id"), nullable=False)
    destination_id = Column(Integer, ForeignKey("destinations.id"), nullable=False)
    day_number = Column(Integer, nullable=False)
    visit_time = Column(String(50))                 # "morning", "afternoon", etc.
    suggested_duration_hours = Column(Float)
    reason = Column(Text)                           # Why this was selected
    crowd_level = Column(String(20))
    sustainability_note = Column(Text)

    itinerary = relationship("Itinerary", back_populates="stops")
    destination = relationship("Destination")


# ─── Artisans ────────────────────────────────────────────────────────────────

class Artisan(Base):
    __tablename__ = "artisans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    name = Column(String(150), nullable=False)
    bio = Column(Text)
    location = Column(String(200))
    latitude = Column(Float)
    longitude = Column(Float)
    category = Column(String(100))  # embroidery, pottery, weaving, etc.
    speciality = Column(String(200))
    profile_image = Column(String(500))
    is_available = Column(Boolean, default=True)
    rating = Column(Float, default=4.5)
    contact_info = Column(JSON, default=dict)
    data_label = Column(String(20), default="DEMO")

    experiences = relationship("CommunityExperience", back_populates="artisan")


class CommunityExperience(Base):
    __tablename__ = "community_experiences"

    id = Column(Integer, primary_key=True, index=True)
    artisan_id = Column(Integer, ForeignKey("artisans.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(100))
    price_per_person = Column(Float)
    max_capacity = Column(Integer, default=10)
    duration_hours = Column(Float, default=2.0)
    is_available = Column(Boolean, default=True)
    languages = Column(JSON, default=list)
    data_label = Column(String(20), default="DEMO")

    artisan = relationship("Artisan", back_populates="experiences")
    bookings = relationship("Booking", back_populates="experience")


# ─── Bookings ─────────────────────────────────────────────────────────────────

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    tourist_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    experience_id = Column(Integer, ForeignKey("community_experiences.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    group_size = Column(Integer, default=1)
    status = Column(Enum(BookingStatus), default=BookingStatus.pending)
    total_price = Column(Float)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    tourist = relationship("User", back_populates="bookings")
    experience = relationship("CommunityExperience", back_populates="bookings")


# ─── Alerts ───────────────────────────────────────────────────────────────────

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    destination_id = Column(Integer, ForeignKey("destinations.id"), nullable=True)
    alert_type = Column(String(50))   # overcrowding, ecological, infrastructure, weather
    title = Column(String(200))
    message = Column(Text, nullable=False)
    severity = Column(Enum(AlertSeverity), default=AlertSeverity.info)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

    destination = relationship("Destination", back_populates="alerts")


# ─── AI Interactions ──────────────────────────────────────────────────────────

class AIInteraction(Base):
    __tablename__ = "ai_interactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    agent = Column(String(100))      # which agent handled this
    query = Column(Text, nullable=False)
    response = Column(Text)
    language = Column(String(20), default="en")
    session_id = Column(String(100))
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="ai_interactions")
