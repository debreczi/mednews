"""Performance tests (AC-10): API response < 200ms with 1000 articles."""
import time
import pytest
from backend.models.article import Article


def _seed_articles(db, n=1000):
    """Insert n articles into the test DB."""
    db.bulk_insert_mappings(Article, [
        {
            "url": f"https://perf.test/article-{i}",
            "original_title": f"Performance Test Article {i}",
            "mednews_title": f"Perf title {i}",
            "summary": "Summary text for performance testing.",
            "relevance_score": 7.0,
            "enrichment_status": "complete",
            "source_id": None,
        }
        for i in range(n)
    ])
    db.commit()


class TestApiPerformance:
    def test_articles_list_under_200ms(self, client, db):
        """AC-10: GET /articles responds in < 200ms with 1000 articles in DB."""
        _seed_articles(db, 1000)

        # Warm-up request
        client.get("/articles")

        # Measure 5 requests and take the mean
        times = []
        for _ in range(5):
            start = time.perf_counter()
            r = client.get("/articles")
            elapsed_ms = (time.perf_counter() - start) * 1000
            assert r.status_code == 200
            times.append(elapsed_ms)

        mean_ms = sum(times) / len(times)
        assert mean_ms < 200, f"Mean response time {mean_ms:.1f}ms exceeds 200ms threshold"

    def test_search_under_200ms(self, client, db):
        """AC-10: GET /search responds in < 200ms with 1000 articles in DB."""
        _seed_articles(db, 1000)

        # Warm-up
        client.get("/search?q=Performance")

        times = []
        for _ in range(5):
            start = time.perf_counter()
            r = client.get("/search?q=Performance")
            elapsed_ms = (time.perf_counter() - start) * 1000
            assert r.status_code == 200
            times.append(elapsed_ms)

        mean_ms = sum(times) / len(times)
        assert mean_ms < 200, f"Mean search response {mean_ms:.1f}ms exceeds 200ms threshold"
