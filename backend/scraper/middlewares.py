"""Custom Scrapy middlewares."""
import logging

logger = logging.getLogger(__name__)


class RateLimitMiddleware:
    """Log rate limit responses (429) for monitoring."""

    def process_response(self, request, response, spider):
        if response.status == 429:
            logger.warning(f"[RateLimit] 429 on {request.url}")
        return response
