import os
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

env_file = BASE_DIR / ".env"
load_dotenv(env_file)


class Config:
    # App
    APP_NAME = os.getenv("APP_NAME", "MyApp")
    APP_ENV: str = os.getenv("APP_ENV", "development")
    # Cache
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    # URLs
    RESET_PASSWORD_URL: str = os.getenv(
        "RESET_PASSWORD_URL", "http://localhost:8000/api/v1/auth/reset-password"
    )
    SIGNUP_URL: str = os.getenv(
        "SIGNUP_URL", "http://localhost:8000/api/v1/auth/register-with-token"
    )
