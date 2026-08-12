"""
Application configuration — reads from .env file via pydantic-settings.
All secrets must be set as environment variables; never hard-code them here.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    app_name: str = "Smart Rann of Kutch Eco-Tourism Planner"
    app_version: str = "1.0.0"
    app_env: str = "development"
    demo_mode: bool = True

    # Security
    secret_key: str = "change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    # Database
    database_url: str = "sqlite:///./kutch_tourism.db"

    # IBM Granite LLM
    ibm_api_key: str = ""
    ibm_project_id: str = ""
    ibm_api_url: str = "https://us-south.ml.cloud.ibm.com"
    ibm_granite_model_id: str = "ibm/granite-3-8b-instruct"

    # Groq LLM (fallback / alternative)
    groq_api_key: str = ""
    groq_model_id: str = "llama-3.3-70b-versatile"
    groq_api_url: str = "https://api.groq.com/openai/v1/chat/completions"

    # Carrying Capacity Weights (configurable by admin)
    cc_weight_tourist_load: float = 0.30
    cc_weight_water_stress: float = 0.20
    cc_weight_waste_stress: float = 0.15
    cc_weight_infrastructure: float = 0.15
    cc_weight_ecological_risk: float = 0.20

    # Thresholds
    cc_low_threshold: int = 40
    cc_moderate_threshold: int = 60
    cc_high_threshold: int = 80

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
