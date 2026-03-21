"""Groq API enrichment service.

Enriches articles with AI-generated Hungarian content:
- mednews_title: humorous/cynical title (max 80 chars)
- summary: 2-3 sentence humorous summary (respectful if tragic)
- link_text: Hungarian CTA with original title (max 40 chars)

Batch processes articles to minimise API calls.
Retries up to 3 times on failure; falls back to original_title on final failure.
"""
import asyncio
import json
import logging
import re
from typing import Any

from groq import AsyncGroq

from ..config import settings

logger = logging.getLogger(__name__)

# Pre-enrichment tragic keyword check — avoids wasting tokens on a detection call
TRAGIC_KEYWORDS = [
    "halál", "elhunyt", "meghalt", "tragédia", "elhalálozás",
    "gyász", "katasztrófa", "áldozat", "súlyos sérülés", "halálos",
    "merénylet", "tömegszerencsétlenség", "tömeges halál",
]

BATCH_SIZE = 10
MAX_RETRIES = 3
RETRY_DELAY = 2.0  # seconds


def is_tragic(text: str) -> bool:
    """True if the article title/content contains tragic keywords."""
    lower = text.lower()
    return any(kw in lower for kw in TRAGIC_KEYWORDS)


def _build_enrichment_prompt(articles: list[dict]) -> str:
    """Build the batch enrichment prompt for Groq."""
    articles_json = json.dumps(
        [{"id": a["_idx"], "title": a["original_title"], "tragic": a["_tragic"]}
         for a in articles],
        ensure_ascii=False,
        indent=2,
    )
    return f"""Te egy magyar egészségügyi IT hírportál szerkesztője vagy, aki humoros és cinikus cikkeket ír szakembereknek.

Kaptál {len(articles)} cikket. Minden cikkhez generálj:
1. "mednews_title": Szellemes, humoros vagy cinikus magyar cím (max 80 karakter). Ha a cikk szomorú/tragikus (tragic=true), legyen tisztelettudó és komoly.
2. "summary": 2-3 mondatos magyar összefoglaló. Ha tragic=false: legyen szellemes, ironikus, de informatív — az olvasónak NE kelljen elolvasnia az eredetit. Ha tragic=true: legyen tisztelettudó, tárgyilagos, humor nélkül.
3. "link_text": Magyar CTA szöveg, max 40 karakter, amely tartalmaz egy utalást az eredeti cikkre. Pl: "Ha tényleg érdekel, itt az eredeti:"

Válaszolj KIZÁRÓLAG valid JSON tömbként, semmi mást ne írj:
[
  {{"id": 0, "mednews_title": "...", "summary": "...", "link_text": "..."}},
  ...
]

Cikkek:
{articles_json}"""


def _build_scoring_prompt(articles: list[dict]) -> str:
    """Build batch scoring prompt — scores relevance 1-10 for Hungarian medical IT pros."""
    articles_json = json.dumps(
        [{"id": a["_idx"], "title": a["original_title"]}
         for a in articles],
        ensure_ascii=False,
        indent=2,
    )
    return f"""Értékeld az alábbi cikkek relevanciáját 1-10 skálán magyar egészségügyi IT szakemberek számára.
10 = rendkívül releváns (egészségügyi IT, digitalizáció, orvosi szoftver, AI az egészségügyben, EESZT, NEAK)
5  = közepesen releváns (általános egészségügy, gyógyszer, kórház)
1  = nem releváns (politika, sport, szórakoztatás)

Válaszolj KIZÁRÓLAG valid JSON tömbként:
[{{"id": 0, "score": 7.5}}, ...]

Cikkek:
{articles_json}"""


async def _call_groq(prompt: str, model: str = "llama-3.3-70b-versatile") -> str:
    """Single Groq API call with fallback model on rate limit."""
    client = AsyncGroq(api_key=settings.groq_api_key)
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=4096,
        )
        return response.choices[0].message.content
    except Exception as e:
        if "rate_limit" in str(e).lower() and model != "llama-3.1-8b-instant":
            logger.warning("[Groq] Rate limit hit — falling back to llama-3.1-8b-instant")
            return await _call_groq(prompt, model="llama-3.1-8b-instant")
        raise


def _extract_json(text: str) -> Any:
    """Extract JSON array from Groq response (handles markdown code fences)."""
    # Strip markdown code fences if present
    text = re.sub(r"```(?:json)?\s*", "", text).strip()
    # Find the JSON array
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        return json.loads(match.group())
    return json.loads(text)


async def _enrich_batch(batch: list[dict]) -> list[dict]:
    """Enrich one batch of articles, with retry logic."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            raw = await _call_groq(_build_enrichment_prompt(batch))
            results = _extract_json(raw)
            # Map results back by id
            by_id = {r["id"]: r for r in results}
            for article in batch:
                r = by_id.get(article["_idx"], {})
                article["mednews_title"] = (r.get("mednews_title") or article["original_title"])[:80]
                article["summary"] = r.get("summary") or ""
                article["link_text"] = (r.get("link_text") or "Az eredeti cikk itt olvasható:")[:40]
                article["enrichment_status"] = "complete"
            return batch
        except Exception as e:
            logger.warning(f"[Enrichment] Attempt {attempt}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES:
                await asyncio.sleep(RETRY_DELAY * attempt)

    # Final fallback — use original title
    logger.error("[Enrichment] All retries exhausted — falling back to original titles")
    for article in batch:
        article["mednews_title"] = article["original_title"]
        article["summary"] = ""
        article["link_text"] = "Az eredeti cikk itt olvasható:"
        article["enrichment_status"] = "failed"
    return batch


async def enrich_articles(articles: list[dict]) -> list[dict]:
    """Enrich articles in batches. Modifies dicts in-place and returns them."""
    if not articles:
        return articles

    # Tag each article with index and tragic flag
    for i, a in enumerate(articles):
        a["_idx"] = i
        a["_tragic"] = is_tragic(a.get("original_title", "") + " " + a.get("summary", ""))
        a["is_tragic"] = a["_tragic"]

    # Process in batches
    batches = [articles[i:i + BATCH_SIZE] for i in range(0, len(articles), BATCH_SIZE)]
    results = []
    for batch in batches:
        enriched = await _enrich_batch(batch)
        results.extend(enriched)
        if len(batches) > 1:
            await asyncio.sleep(0.5)  # gentle rate limiting between batches

    # Clean up internal keys
    for a in results:
        a.pop("_idx", None)
        a.pop("_tragic", None)

    logger.info(f"[Enrichment] Enriched {len(results)} articles")
    return results


async def log_enrichment_cost(tokens_used: int, model: str = "llama-3.3-70b-versatile"):
    """Estimate and log Groq API cost (approximate pricing)."""
    # Approximate: $0.59 per 1M tokens for llama-3.3-70b
    cost_per_million = 0.59 if "70b" in model else 0.05
    cost = (tokens_used / 1_000_000) * cost_per_million
    logger.info(f"[Enrichment] Tokens used: {tokens_used} | Est. cost: ${cost:.4f}")
    return cost
