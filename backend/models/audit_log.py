from datetime import datetime
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from ..database import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    # scrape_start | scrape_end | enrich_call | source_discovery | api_request
    source_name: Mapped[str | None] = mapped_column(String, nullable=True)
    article_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("articles.id"), nullable=True
    )
    articles_found: Mapped[int | None] = mapped_column(Integer, nullable=True)
    articles_saved: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cost_estimate: Mapped[float | None] = mapped_column(Float, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
