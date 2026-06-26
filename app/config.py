import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Port configuration
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    
    # OpenRouter API settings
    OPENROUTER_API_KEY: str = ""
    MODEL_NAME: str = "google/gemini-2.5-flash"  # sensible default
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    
    # Path settings
    BASE_DIR: Path = Path(__file__).resolve().parent.parent

    # Threshold for high-value cases
    HIGH_VALUE_THRESHOLD: float = 5000.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
