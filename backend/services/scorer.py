"""Article relevance scoring via xAI Grok API.

Scores articles 1-10 for relevance to Hungarian medical IT professionals.
Batch processes to minimise API calls.
"""
import asyncio
import logging
from typing import Any

from ..config import settings

logger = logging.getLogger(__name__)

BATCH_SIZE = 20
MAX_RETRIES = 3


async def score_articles_batch(articles: list[dict]) -> list[float]:
    """Score a batch of articles. Returns list of scores in same order."""
    from .enrichment import _call_llm, _extract_json, _build_scoring_prompt, RETRY_DELAY

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            raw = await _call_llm(_build_scoring_prompt(articles))
            results = _extract_json(raw)
            by_id = {r["id"]: float(r["score"]) for r in results}
            return [by_id.get(a["_idx"], 5.0) for a in articles]
        except Exception as e:
            logger.warning(f"[Scorer] Attempt {attempt}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES:
                await asyncio.sleep(RETRY_DELAY * attempt)

    # Fallback: return neutral score so threshold filter decides
    logger.error("[Scorer] All retries exhausted — returning neutral scores (5.0)")
    return [5.0] * len(articles)


async def score_article(title: str, content: str = "") -> float:
    """Score a single article. Used for ad-hoc scoring outside batch pipeline."""
    articles = [{"_idx": 0, "original_title": title}]
    scores = await score_articles_batch(articles)
    return scores[0]


async def score_and_filter(articles: list[dict], threshold: float) -> list[dict]:
    """Score articles in batches, attach scores, return only those >= threshold."""
    if not articles:
        return []

    for i, a in enumerate(articles):
        a["_idx"] = i

    batches = [articles[i:i + BATCH_SIZE] for i in range(0, len(articles), BATCH_SIZE)]
    all_scores: list[float] = []
    for batch in batches:
        scores = await score_articles_batch(batch)
        all_scores.extend(scores)
        if len(batches) > 1:
            await asyncio.sleep(0.3)

    saved = []
    for article, score in zip(articles, all_scores):
        article["relevance_score"] = score
        article.pop("_idx", None)
        if score >= threshold:
            saved.append(article)

    logger.info(
        f"[Scorer] {len(saved)}/{len(articles)} articles passed threshold {threshold}"
    )
    return saved
