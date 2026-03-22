from datetime import datetime
from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)  # portal | rss | social | international
    region: Mapped[str] = mapped_column(String(2), nullable=False, default="HU")  # HU | EU | US
    spider_name: Mapped[str] = mapped_column(String, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_scraped: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    articles_total: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    articles_saved: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    articles: Mapped[list["Article"]] = relationship("Article", back_populates="source")
