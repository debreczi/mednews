from datetime import datetime
from pydantic import BaseModel


class AuditLogOut(BaseModel):
    id: int
    timestamp: datetime
    event_type: str
    source_name: str | None
    article_id: int | None
    articles_found: int | None
    articles_saved: int | None
    tokens_used: int | None
    cost_estimate: float | None
    error_message: str | None
    duration_ms: int | None

    model_config = {"from_attributes": True}


class PaginatedAuditLog(BaseModel):
    logs: list[AuditLogOut]
    next_cursor: int | None
