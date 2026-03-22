"""Tests for AI enrichment service (AC-5, AC-6, AC-7)."""
import json
import pytest
from unittest.mock import AsyncMock, patch

from backend.services.enrichment import enrich_articles


# ── Enrichment with mocked LLM (AC-5, AC-7) ───────────────────────────────────

MOCK_LLM_RESPONSE = json.dumps([
    {
        "id": 0,
        "mednews_title": "AI felszámolja az orvosi bürokráciát (spoiler: nem)",
        "summary": "Egy új AI rendszer állítólag megoldja az összes egészségügyi IT problémát.",
        "link_text": "Az eredeti cikk itt olvasható:",
        "is_tragic": False,
    },
    {
        "id": 1,
        "mednews_title": "EESZT megint frissül, mindenki örül (nem)",
        "summary": "Az EESZT rendszer újabb frissítést kap.",
        "link_text": "Ha tényleg érdekel:",
        "is_tragic": False,
    },
])


@pytest.mark.asyncio
async def test_enrich_articles_success():
    """AC-5: All articles receive mednews_title after enrichment."""
    articles = [
        {"original_title": "New AI system in healthcare"},
        {"original_title": "EESZT system update"},
    ]
    mock_response = AsyncMock(return_value=MOCK_LLM_RESPONSE)

    with patch("backend.services.enrichment._call_llm", mock_response):
        result = await enrich_articles(articles)

    assert len(result) == 2
    for a in result:
        assert a.get("mednews_title") is not None
        assert a.get("mednews_title") != ""
        assert a.get("enrichment_status") == "complete"


@pytest.mark.asyncio
async def test_enrichment_fallback_on_failure():
    """AC-7: On 3 failures, mednews_title falls back to original_title."""
    articles = [{"original_title": "Eredeti cím itt"}]

    with patch("backend.services.enrichment._call_llm", side_effect=Exception("LLM 500")):
        result = await enrich_articles(articles)

    assert result[0]["mednews_title"] == "Eredeti cím itt"
    assert result[0]["enrichment_status"] == "failed"


@pytest.mark.asyncio
async def test_tragic_article_flagged_by_llm():
    """AC-6: LLM determines tragic articles and flags is_tragic=True."""
    articles = [{"original_title": "Halál a kórházban — szomorú esemény"}]

    mock_response = AsyncMock(return_value=json.dumps([
        {"id": 0, "mednews_title": "Szomorú esemény", "summary": "Tisztelettudó összefoglaló.",
         "link_text": "Eredeti cikk:", "is_tragic": True}
    ]))

    with patch("backend.services.enrichment._call_llm", mock_response):
        result = await enrich_articles(articles)

    assert result[0]["is_tragic"] is True


@pytest.mark.asyncio
async def test_non_tragic_article_not_flagged():
    articles = [{"original_title": "Új telemedicina platform indul"}]

    mock_response = AsyncMock(return_value=json.dumps([
        {"id": 0, "mednews_title": "Megint telefonálunk orvossal", "summary": "Humoros összefoglaló.",
         "link_text": "Eredeti:", "is_tragic": False}
    ]))

    with patch("backend.services.enrichment._call_llm", mock_response):
        result = await enrich_articles(articles)

    assert result[0]["is_tragic"] is False


@pytest.mark.asyncio
async def test_mednews_title_truncated_to_80_chars():
    """mednews_title must not exceed 80 characters."""
    long_title = "X" * 200
    articles = [{"original_title": "Short title"}]

    mock_response = AsyncMock(return_value=json.dumps([
        {"id": 0, "mednews_title": long_title, "summary": "Summary.",
         "link_text": "Link:", "is_tragic": False}
    ]))

    with patch("backend.services.enrichment._call_llm", mock_response):
        result = await enrich_articles(articles)

    assert len(result[0]["mednews_title"]) <= 80


@pytest.mark.asyncio
async def test_empty_articles_list():
    result = await enrich_articles([])
    assert result == []


@pytest.mark.asyncio
async def test_retry_then_succeed():
    """Succeeds on second attempt after one failure."""
    articles = [{"original_title": "Test article"}]
    call_count = 0

    async def flaky_llm(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise Exception("Temporary error")
        return json.dumps([
            {"id": 0, "mednews_title": "Recovered title", "summary": "OK.",
             "link_text": "Link:", "is_tragic": False}
        ])

    with patch("backend.services.enrichment._call_llm", flaky_llm):
        result = await enrich_articles(articles)

    assert result[0]["mednews_title"] == "Recovered title"
    assert result[0]["enrichment_status"] == "complete"
    assert call_count == 2
