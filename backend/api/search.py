from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import case, select, text
from datetime import date

from ..database import get_db
from ..models.article import Article
from ..schemas.article import ArticleOut

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=list[ArticleOut])
def search_articles(
    q: str | None = Query(None, min_length=1),
    from_date: date | None = None,
    to_date: date | None = None,
    after: int | None = None,
    db: Session = Depends(get_db),
):
    """Full-text search with optional date range filter."""
    if q:
        # Use FTS5 for keyword search
        fts_query = text("""
            SELECT a.id FROM articles a
            JOIN articles_fts ON articles_fts.rowid = a.id
            WHERE articles_fts MATCH :q
            ORDER BY a.id DESC
            LIMIT 100
        """)
        result = db.execute(fts_query, {"q": q})
        ids = [row[0] for row in result]
        if not ids:
            return []
        _sort = case((Article.date_published.isnot(None), Article.date_published), else_=Article.date_collected)
        stmt = select(Article).options(joinedload(Article.source)).where(Article.id.in_(ids)).order_by(_sort.desc())
    else:
        _sort = case((Article.date_published.isnot(None), Article.date_published), else_=Article.date_collected)
        stmt = select(Article).options(joinedload(Article.source)).order_by(_sort.desc())

    if from_date:
        stmt = stmt.where(Article.date_published >= from_date)
    if to_date:
        stmt = stmt.where(Article.date_published <= to_date)
    if after:
        stmt = stmt.where(Article.id < after)

    stmt = stmt.limit(25)
    return db.scalars(stmt).all()
