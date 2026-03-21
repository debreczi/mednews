"""FastAPI application entry point."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db
from .services.scheduler import start_scheduler, stop_scheduler
from .api import articles, search, admin

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("[Startup] Initializing database...")
    init_db()
    logger.info("[Startup] Starting scheduler...")
    start_scheduler()
    logger.info("[Startup] MedNews API ready.")
    yield
    logger.info("[Shutdown] Stopping scheduler...")
    stop_scheduler()
    logger.info("[Shutdown] Done.")


app = FastAPI(
    title="MedNews API",
    description="Hungarian medical news aggregator",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:4173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(articles.router)
app.include_router(search.router)
app.include_router(admin.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "mednews-api"}
