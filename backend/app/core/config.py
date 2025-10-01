from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    REDIS_URL: str

    # APIs
    OPENAI_API_KEY: str
    GOOGLE_MAPS_API_KEY: str
    EVOLUTION_API_URL: str
    EVOLUTION_API_KEY: str

    # Security
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    # App
    WEBHOOK_URL: str
    TRIAL_DAYS: int = 7

    # Cache
    ADDRESS_CACHE_DAYS: int = 30

    class Config:
        env_file = ".env"

settings = Settings()