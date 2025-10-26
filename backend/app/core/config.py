from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    REDIS_URL: str

    # APIs
    OPENAI_API_KEY: str
    GOOGLE_MAPS_API_KEY: Optional[str] = None
    EVOLUTION_API_URL: str
    EVOLUTION_API_KEY: str

    # Security
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    # App
    WEBHOOK_URL: str
    TRIAL_DAYS: int = 7
    ENVIRONMENT: str = "development"

    # Cache
    ADDRESS_CACHE_DAYS: int = 30

    # Fine-tuned Models
    FINETUNED_EXTRACTOR_MODEL: str = "ft:gpt-4.1-mini-2025-04-14:carvalho-ia:botgas:CTt20bmy"
    USE_FINETUNED_EXTRACTOR: bool = True  # Toggle para A/B test

    class Config:
        env_file = ".env"

settings = Settings()