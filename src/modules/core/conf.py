import os
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

env_file = BASE_DIR / ".env"
load_dotenv(env_file)

PRIVATE_KEY_PATH = BASE_DIR / "keys" / "private.pem"
PUBLIC_KEY_PATH = BASE_DIR / "keys" / "public.pem"


class Config:
    # App
    APP_NAME = os.getenv("APP_NAME", "MyApp")
    APP_ENV: str = os.getenv("APP_ENV", "development")

    # JWT
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "RS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("", 15))
    REFRESH_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("", 43200))
    ROTATE_THRESHOLD_MINUTES: int = int(os.getenv("", 4320))
    # Load keys
    with open(PRIVATE_KEY_PATH, "r") as f:
        JWT_PRIVATE_KEY: str = f.read()

    with open(PUBLIC_KEY_PATH, "r") as f:
        JWT_PUBLIC_KEY: str = f.read()

    # Cache
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
