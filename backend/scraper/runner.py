"""CrawlerRunner bridge — runs all active Scrapy spiders inside the FastAPI process.

Note: Scrapy uses Twisted's reactor. We use CrawlerRunner (not CrawlerProcess) so it
can share the asyncio event loop configured in scrapy settings via TWISTED_REACTOR.
Actual per-spider stats are tracked by DatabasePipeline; runner returns aggregate totals.
"""
# Must install the asyncio reactor before any other Twisted/Scrapy imports
try:
    from twisted.internet import asyncioreactor
    asyncioreactor.install()
except Exception:
    pass  # Already installed

import importlib
import inspect
import logging
import pkgutil
from typing import Any

logger = logging.getLogger(__name__)


def _find_spider_class(spider_name: str):
    """Locate a Scrapy spider class by its `name` attribute."""
    import backend.scraper.spiders as spiders_pkg
    from .spiders.base_spider import BaseSpider

    for _, modname, _ in pkgutil.walk_packages(
        path=spiders_pkg.__path__,
        prefix=spiders_pkg.__name__ + ".",
        onerror=lambda x: None,
    ):
        try:
            mod = importlib.import_module(modname)
            for _, obj in inspect.getmembers(mod, inspect.isclass):
                if (
                    issubclass(obj, BaseSpider)
                    and obj is not BaseSpider
                    and getattr(obj, "name", None) == spider_name
                ):
                    return obj
        except Exception:
            pass
    return None


async def run_all_spiders() -> dict[str, Any]:
    """Run all active sources through their configured spiders.

    Groups sources by spider_name, then runs each spider class once per source URL.
    Returns aggregate stats: {"found": N, "saved": N, "errors": N}
    """
    from ..database import SessionLocal
    from ..models.source import Source
    from sqlalchemy import select

    with SessionLocal() as db:
        sources = list(db.scalars(select(Source).where(Source.active == True)).all())

    if not sources:
        logger.warning("[Runner] No active sources found")
        return {"found": 0, "saved": 0, "errors": 0}

    # Group sources by spider_name
    by_spider: dict[str, list] = {}
    for src in sources:
        by_spider.setdefault(src.spider_name, []).append(src)

    stats = {"found": 0, "saved": 0, "errors": 0}

    for spider_name, srcs in by_spider.items():
        spider_cls = _find_spider_class(spider_name)
        if not spider_cls:
            logger.warning(f"[Runner] No spider class for name '{spider_name}' — skipping {len(srcs)} sources")
            stats["errors"] += len(srcs)
            continue

        for src in srcs:
            try:
                result = await _crawl_source(spider_cls, src)
                stats["found"] += result.get("found", 0)
                stats["saved"] += result.get("saved", 0)
            except Exception as e:
                stats["errors"] += 1
                logger.error(f"[Runner] {spider_name} on {src.url} failed: {e}")

    logger.info(f"[Runner] Run complete: {stats}")
    return stats


async def _crawl_source(spider_cls, source) -> dict[str, Any]:
    """Run one spider instance for one source using CrawlerRunner + asyncio bridge."""
    from scrapy.crawler import CrawlerRunner
    from scrapy.utils.project import get_project_settings
    import asyncio

    settings = get_project_settings()
    runner = CrawlerRunner(settings)

    # CrawlerRunner returns a Deferred; wrap it for asyncio
    deferred = runner.crawl(spider_cls, url=source.url, source_id=source.id)

    # Convert Twisted Deferred to asyncio Future
    loop = asyncio.get_event_loop()
    future: asyncio.Future = loop.create_future()

    def on_success(result):
        if not future.done():
            loop.call_soon_threadsafe(future.set_result, result)

    def on_error(failure):
        if not future.done():
            loop.call_soon_threadsafe(future.set_exception, Exception(str(failure)))

    deferred.addCallback(on_success)
    deferred.addErrback(on_error)

    try:
        await asyncio.wait_for(future, timeout=300)  # 5 minute timeout per source
    except asyncio.TimeoutError:
        logger.warning(f"[Runner] Spider timeout on {source.url}")
    except Exception as e:
        logger.error(f"[Runner] Spider error on {source.url}: {e}")

    # Stats are tracked by DatabasePipeline; return zeros here
    return {"found": 0, "saved": 0}
