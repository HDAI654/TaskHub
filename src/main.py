from fastapi import FastAPI
from src.logging_config import setup_logging
from contextlib import asynccontextmanager
from src.modules.core.redis_client import close_redis_client
import logging
from src.modules.core.conf import Config

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_redis_client()


app = FastAPI(
    lifespan=lifespan,
)

logging.info("TaskHub started successfully")


@app.get("/", tags=["Root"])
async def read_root():
    return {"message": f"Welcome to {Config.APP_NAME}"}


#app.include_router(router_v1_auth)
