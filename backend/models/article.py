from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    url: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    original_title: Mapped[str] = mapped_column(Text, nullable=False)
    mednews_title: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    link_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String, nullable=True)
    date_collected: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    date_published: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    relevance_score: Mapped[float] = mapped_column(Float, nullable=False)
    is_tragic: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    enrichment_status: Mapped[str] = mapped_column(
        String, default="pending", nullable=False
    )
    source_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("sources.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    source: Mapped["Source | None"] = relationship("Source", back_populates="articles")

    @hybrid_property
    def source_region(self) -> str | None:
        return self.source.region if self.source else None
