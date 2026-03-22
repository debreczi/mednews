from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, func

from ..database import get_db
from ..models.article import Article
from ..models.source import Source
from ..schemas.article import ArticleOut, PaginatedArticles

router = APIRouter(prefix="/articles", tags=["articles"])

PAGE_SIZE = 25
HU_RATIO = 0.7  # 70% Hungarian articles


@router.get("", response_model=PaginatedArticles)
def list_articles(after: int | None = None, region: str | None = None, db: Session = Depends(get_db)):
    """Return up to 25 articles, optionally filtered by region."""
    base = select(Article).options(joinedload(Article.source)).order_by(Article.id.desc())
    if after is not None:
        base = base.where(Article.id < after)

    # If a specific region is requested, filter directly
    if region:
        regions = [region] if region != "INTL" else ["EU", "US"]
        query = base.join(Source).where(Source.region.in_(regions)).limit(PAGE_SIZE + 1)
        rows = db.scalars(query).unique().all()
        has_more = len(rows) > PAGE_SIZE
        items = rows[:PAGE_SIZE]
        next_cursor = items[-1].id if has_more and items else None
        total = db.scalar(
            select(func.count()).select_from(Article).join(Source).where(Source.region.in_(regions))
        ) or 0
        return PaginatedArticles(articles=items, next_cursor=next_cursor, total_count=total)

    # Default: ~70% Hungarian / 30% international mix
    hu_limit = int(PAGE_SIZE * HU_RATIO)       # 17
    intl_limit = PAGE_SIZE - hu_limit           # 8

    hu_query = base.join(Source).where(Source.region == "HU").limit(hu_limit + 1)
    hu_rows = db.scalars(hu_query).unique().all()

    intl_query = base.join(Source).where(Source.region != "HU").limit(intl_limit + 1)
    intl_rows = db.scalars(intl_query).unique().all()

    combined = sorted(hu_rows[:hu_limit] + intl_rows[:intl_limit], key=lambda a: a.id, reverse=True)

    if len(combined) < PAGE_SIZE:
        seen_ids = {a.id for a in combined}
        fill_query = base.limit(PAGE_SIZE + 1)
        fill_rows = [a for a in db.scalars(fill_query).unique().all() if a.id not in seen_ids]
        combined = sorted(combined + fill_rows[:PAGE_SIZE - len(combined)], key=lambda a: a.id, reverse=True)

    has_more = len(hu_rows) > hu_limit or len(intl_rows) > intl_limit
    items = combined[:PAGE_SIZE]
    next_cursor = items[-1].id if has_more and items else None
    total = db.scalar(select(func.count()).select_from(Article)) or 0

    return PaginatedArticles(articles=items, next_cursor=next_cursor, total_count=total)


@router.get("/{article_id}", response_model=ArticleOut)
def get_article(article_id: int, db: Session = Depends(get_db)):
    article = db.scalars(
        select(Article).options(joinedload(Article.source)).where(Article.id == article_id)
    ).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article
