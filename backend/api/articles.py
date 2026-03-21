from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from ..database import get_db
from ..models.article import Article
from ..schemas.article import ArticleOut, PaginatedArticles

router = APIRouter(prefix="/articles", tags=["articles"])

PAGE_SIZE = 25


@router.get("", response_model=PaginatedArticles)
def list_articles(after: int | None = None, db: Session = Depends(get_db)):
    """Return up to 25 articles, cursor-paginated by id descending."""
    query = select(Article).order_by(Article.id.desc())
    if after is not None:
        query = query.where(Article.id < after)
    query = query.limit(PAGE_SIZE + 1)

    rows = db.scalars(query).all()
    has_more = len(rows) > PAGE_SIZE
    items = rows[:PAGE_SIZE]
    next_cursor = items[-1].id if has_more and items else None
    total = db.scalar(select(func.count()).select_from(Article)) or 0

    return PaginatedArticles(articles=items, next_cursor=next_cursor, total_count=total)


@router.get("/{article_id}", response_model=ArticleOut)
def get_article(article_id: int, db: Session = Depends(get_db)):
    article = db.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article
