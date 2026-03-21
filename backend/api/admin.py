from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..config import settings
from ..database import get_db
from ..models.source import Source
from ..models.audit_log import AuditLog
from ..schemas.audit_log import AuditLogOut, PaginatedAuditLog

router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin(x_admin_key: str = Header(...)):
    if x_admin_key != settings.admin_api_key:
        raise HTTPException(status_code=403, detail="Invalid admin key")


@router.post("/trigger-scrape", dependencies=[Depends(require_admin)])
async def trigger_scrape():
    """Manually trigger a full scrape cycle."""
    # Dispatcher imported here to avoid circular imports
    from ..services.scheduler import run_scrape_job
    import asyncio
    asyncio.create_task(run_scrape_job())
    return {"status": "scrape job queued"}


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
