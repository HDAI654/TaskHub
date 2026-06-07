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

    # DB
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://user:password@host:port/dbname",
    )
    # Cache
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    # Keys
    with open(PRIVATE_KEY_PATH, "r") as f:
        JWT_PRIVATE_KEY: str = f.read()

    with open(PUBLIC_KEY_PATH, "r") as f:
        JWT_PUBLIC_KEY: str = f.read()

    # JWT
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "RS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 15))
    REFRESH_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES", 43200))
    ROTATE_THRESHOLD_MINUTES: int = int(os.getenv("ROTATE_THRESHOLD_MINUTES", 4320))
    
    

    
