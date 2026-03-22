"""AI-powered source discovery using LLM API.

Weekly job that asks the LLM to identify new Hungarian medical news sources
not already in our database, then adds them.
"""
import logging

logger = logging.getLogger(__name__)

DISCOVERY_PROMPT = """Keress aktív magyar egészségügyi híroldalakat, RSS feedeket és közösségi média oldalakat, amelyek rendszeresen publikálnak egészségügyi, orvosi IT vagy gyógyszeripari híreket.

Meglévő forrásaink URL-jei (ezeket NE add hozzá):
{existing_urls}

Keress legalább 10 ÚJ forrást a következő típusokból:
- Magyar orvosi/egészségügyi hírportálok
- Magyar kórházak/intézmények híroldala
- Magyar egészségügyi IT blogok/portálok
- Fontos európai egészségügyi szervezetek (RSS-sel)
- Egészségügyi AI/tech híroldalak (RSS-sel)

Válaszolj KIZÁRÓLAG valid JSON tömbként:
[
  {{
    "name": "Forrás neve",
    "url": "https://...",
    "type": "portal|rss|social|international",
    "spider_name": "rss_spider"
  }},
  ...
]"""


async def discover_new_sources(existing_urls: list[str]) -> list[dict]:
    """Use LLM to find new Hungarian medical news sources not in our DB."""
    from .enrichment import _call_llm, _extract_json, DEFAULT_MODEL

    urls_sample = "\n".join(existing_urls[:30])
    prompt = DISCOVERY_PROMPT.format(existing_urls=urls_sample)

    try:
        raw = await _call_llm(prompt, model=DEFAULT_MODEL)
        candidates = _extract_json(raw)
        existing_set = set(existing_urls)
        new_sources = [s for s in candidates if s.get("url") not in existing_set]
        logger.info(f"[SourceDiscovery] Found {len(new_sources)} new sources")
        return new_sources
    except Exception as e:
        logger.error(f"[SourceDiscovery] Failed: {e}")
        return []


async def run_discovery_and_save() -> int:
    """Full discovery cycle: find new sources and save to DB."""
    from ..database import SessionLocal
    from ..models.source import Source
    from sqlalchemy import select

    with SessionLocal() as db:
        existing_urls = list(db.scalars(select(Source.url)).all())

    new_sources = await discover_new_sources(existing_urls)
    if not new_sources:
        return 0

    added = 0
    with SessionLocal() as db:
        existing_set = set(db.scalars(select(Source.url)).all())
        for src in new_sources:
            if src.get("url") and src["url"] not in existing_set:
                db.add(Source(
                    name=src.get("name", src["url"]),
                    url=src["url"],
                    type=src.get("type", "portal"),
                    spider_name=src.get("spider_name", "rss_spider"),
                    active=True,
                ))
                added += 1
        db.commit()

    logger.info(f"[SourceDiscovery] Added {added} new sources to DB")
    return added
