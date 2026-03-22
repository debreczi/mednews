import asyncio
import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..config import settings
from ..database import get_db
from ..models.article import Article
from ..models.source import Source
from ..models.audit_log import AuditLog
from ..schemas.audit_log import AuditLogOut, PaginatedAuditLog

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin(x_admin_key: str = Header(...)):
    if x_admin_key != settings.admin_api_key:
        raise HTTPException(status_code=403, detail="Invalid admin key")


@router.post("/trigger-scrape", dependencies=[Depends(require_admin)])
async def trigger_scrape():
    """Manually trigger a full scrape cycle."""
    from ..services.scheduler import run_scrape_job
    asyncio.create_task(run_scrape_job())
    return {"status": "scrape job queued"}


@router.post("/re-enrich", dependencies=[Depends(require_admin)])
async def re_enrich(
    status: str = Query(
        "all",
        description="Which articles to re-enrich: 'all', 'failed', or 'pending'",
    ),
    limit: int = Query(
        0,
        description="Max articles to re-enrich (0 = all matching)",
    ),
    db: Session = Depends(get_db),
):
    """Re-run LLM enrichment on existing articles in the database."""
    stmt = select(Article).order_by(Article.id.desc())
    if status == "failed":
        stmt = stmt.where(Article.enrichment_status == "failed")
    elif status == "pending":
        stmt = stmt.where(Article.enrichment_status == "pending")
    # 'all' re-enriches everything
    if limit > 0:
        stmt = stmt.limit(limit)

    articles = list(db.scalars(stmt).all())
    if not articles:
        return {"status": "no articles matched", "filter": status, "count": 0}

    # Build dicts for the enrichment service
    to_enrich = [
        {"original_title": a.original_title, "_db_id": a.id}
        for a in articles
    ]

    async def _run():
        try:
            from ..services.enrichment import enrich_articles
            enriched = await enrich_articles(to_enrich)

            # Write results back to DB
            from ..database import SessionLocal
            updated = 0
            with SessionLocal() as session:
                for item in enriched:
                    db_id = item.get("_db_id")
                    if db_id is None:
                        continue
                    art = session.get(Article, db_id)
                    if not art:
                        continue
                    art.mednews_title = item.get("mednews_title", art.mednews_title)
                    art.summary = item.get("summary", art.summary)
                    art.link_text = item.get("link_text", art.link_text)
                    art.is_tragic = item.get("is_tragic", art.is_tragic)
                    art.enrichment_status = item.get("enrichment_status", art.enrichment_status)
                    updated += 1
                session.commit()
            logger.info(f"[Re-enrich] Completed {updated}/{len(enriched)} articles")
        except Exception as e:
            logger.error(f"[Re-enrich] Failed: {e}", exc_info=True)

    count = len(to_enrich)
    await _run()
    return {"status": "re-enrichment complete", "filter": status, "count": count}


@router.post("/backfill-images", dependencies=[Depends(require_admin)])
async def backfill_images(db: Session = Depends(get_db)):
    """Fetch og:image for articles that have no image_url."""
    from ..scraper.runner import _fetch_og_image

    articles = list(db.scalars(
        select(Article).where(Article.image_url.is_(None)).order_by(Article.id.desc())
    ).all())

    if not articles:
        return {"status": "no articles need images", "count": 0}

    import asyncio
    tasks = [_fetch_og_image(a.url) for a in articles]
    results = await asyncio.gather(*tasks)

    updated = 0
    for art, img in zip(articles, results):
        if img:
            art.image_url = img
            updated += 1
    db.commit()

    logger.info(f"[Backfill] Updated {updated}/{len(articles)} article images")
    return {"status": "backfill complete", "checked": len(articles), "updated": updated}


@router.get("/logs", response_model=PaginatedAuditLog, dependencies=[Depends(require_admin)])
def get_logs(after: int | None = None, db: Session = Depends(get_db)):
    stmt = select(AuditLog).order_by(AuditLog.id.desc())
    if after:
        stmt = stmt.where(AuditLog.id < after)
    stmt = stmt.limit(50)
    rows = db.scalars(stmt).all()
    has_more = len(rows) == 50
    next_cursor = rows[-1].id if has_more and rows else None
    return PaginatedAuditLog(logs=rows, next_cursor=next_cursor)


@router.get("/sources", dependencies=[Depends(require_admin)])
def list_sources(db: Session = Depends(get_db)):
    return db.scalars(select(Source).order_by(Source.name)).all()


@router.put("/sources/{source_id}", dependencies=[Depends(require_admin)])
def update_source(source_id: int, active: bool, db: Session = Depends(get_db)):
    source = db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    source.active = active
    db.commit()
    return {"id": source_id, "active": active}
