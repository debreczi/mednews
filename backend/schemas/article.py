from datetime import datetime
from pydantic import BaseModel


class ArticleOut(BaseModel):
    id: int
    url: str
    original_title: str
    mednews_title: str | None
    summary: str | None
    link_text: str | None
    source_text: str | None
    image_url: str | None
    date_collected: datetime
    date_published: datetime | None
    relevance_score: float
    is_tragic: bool
    enrichment_status: str
    source_id: int | None

    model_config = {"from_attributes": True}


class PaginatedArticles(BaseModel):
    articles: list[ArticleOut]
    next_cursor: int | None  # None means no more pages
    total_count: int
