"""FastAPI application entry point."""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

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
    # Auto-seed sources (idempotent — only inserts new ones)
    from .seeds.sources import seed_sources
    from .database import SessionLocal
    with SessionLocal() as db:
        n = seed_sources(db)
        if n:
            logger.info(f"[Startup] Seeded {n} new sources")
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
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(articles.router)
app.include_router(search.router)
app.include_router(admin.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "mednews-api"}


# Serve Vue SPA — must come after all API routes
_dist = Path(__file__).parent.parent / "frontend" / "dist"
if _dist.exists():
    app.mount("/assets", StaticFiles(directory=_dist / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa_fallback(full_path: str):
        """Return index.html for all non-API routes (Vue Router)."""
        return FileResponse(_dist / "index.html")
