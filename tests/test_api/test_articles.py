"""API tests for /articles and /search endpoints."""
from datetime import datetime, timezone

import pytest
from backend.models.article import Article


def make_article(db, **kwargs):
    """Helper: insert an Article and return it."""
    defaults = {
        "url": f"https://example.com/{kwargs.get('url', 'article-1')}",
        "original_title": "Test Article",
        "mednews_title": "Funny Test Article",
        "summary": "A test summary.",
        "link_text": "Read the original here",
        "relevance_score": 7.5,
        "is_tragic": False,
        "enrichment_status": "complete",
        "date_collected": datetime.now(timezone.utc),
    }
    defaults.update(kwargs)
    article = Article(**defaults)
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


class TestArticlesList:
    def test_empty_list(self, client):
        r = client.get("/articles")
        assert r.status_code == 200
        data = r.json()
        assert data["articles"] == []
        assert data["next_cursor"] is None
        assert data["total_count"] == 0

    def test_returns_articles(self, client, db):
        make_article(db, url="art-list-1", original_title="Article 1")
        make_article(db, url="art-list-2", original_title="Article 2")
        r = client.get("/articles")
        assert r.status_code == 200
        data = r.json()
        assert len(data["articles"]) == 2
        assert data["total_count"] == 2

    def test_max_25_per_page(self, client, db):
        for i in range(30):
            make_article(db, url=f"bulk-{i}")
        r = client.get("/articles")
        assert r.status_code == 200
        data = r.json()
        assert len(data["articles"]) <= 25
        assert data["next_cursor"] is not None

    def test_cursor_pagination(self, client, db):
        for i in range(30):
            make_article(db, url=f"cursor-{i}")
        # First page
        r1 = client.get("/articles")
        data1 = r1.json()
        assert len(data1["articles"]) == 25
        cursor = data1["next_cursor"]
        assert cursor is not None
        # Second page
        r2 = client.get(f"/articles?after={cursor}")
        data2 = r2.json()
        assert len(data2["articles"]) > 0
        # No overlap
        ids1 = {a["id"] for a in data1["articles"]}
        ids2 = {a["id"] for a in data2["articles"]}
        assert ids1.isdisjoint(ids2)

    def test_article_fields(self, client, db):
        make_article(db, url="fields-test", original_title="Fields Article", mednews_title="Funny Title")
        r = client.get("/articles")
        article = r.json()["articles"][0]
        assert "id" in article
        assert "url" in article
        assert "original_title" in article
        assert "mednews_title" in article
        assert "relevance_score" in article
        assert "is_tragic" in article

    def test_get_by_id(self, client, db):
        a = make_article(db, url="by-id-test")
        r = client.get(f"/articles/{a.id}")
        assert r.status_code == 200
        assert r.json()["id"] == a.id

    def test_get_by_id_not_found(self, client):
        r = client.get("/articles/999999")
        assert r.status_code == 404

    def test_descending_order(self, client, db):
        a1 = make_article(db, url="order-1")
        a2 = make_article(db, url="order-2")
        r = client.get("/articles")
        ids = [a["id"] for a in r.json()["articles"]]
        assert ids[0] > ids[-1]  # descending


class TestSearch:
    def test_empty_search(self, client):
        r = client.get("/search?q=nonexistent_keyword_xyz")
        assert r.status_code == 200
        assert r.json() == []

    def test_no_query_returns_articles(self, client, db):
        make_article(db, url="search-no-q")
        r = client.get("/search")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_date_filter_from(self, client, db):
        old = make_article(
            db, url="date-old",
            date_published=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        new = make_article(
            db, url="date-new",
            date_published=datetime(2025, 6, 1, tzinfo=timezone.utc),
        )
        r = client.get("/search?from_date=2025-01-01")
        data = r.json()
        ids = [a["id"] for a in data]
        assert new.id in ids
        assert old.id not in ids

    def test_date_filter_to(self, client, db):
        old = make_article(
            db, url="date-to-old",
            date_published=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        new = make_article(
            db, url="date-to-new",
            date_published=datetime(2025, 6, 1, tzinfo=timezone.utc),
        )
        r = client.get("/search?to_date=2024-12-31")
        data = r.json()
        ids = [a["id"] for a in data]
        assert old.id in ids
        assert new.id not in ids


class TestDuplicateRejection:
    def test_duplicate_url_raises_integrity_error(self, db):
        """AC-4: Inserting duplicate URL must raise IntegrityError; DB count unchanged."""
        from sqlalchemy.exc import IntegrityError

        a1 = Article(
            url="https://example.com/article-unique",
            original_title="First",
            relevance_score=7.0,
            source_id=None,
        )
        db.add(a1)
        db.commit()

        count_before = db.query(Article).count()

        a2 = Article(
            url="https://example.com/article-unique",  # same URL
            original_title="Second",
            relevance_score=8.0,
            source_id=None,
        )
        db.add(a2)
        with pytest.raises(IntegrityError):
            db.commit()

        db.rollback()
        count_after = db.query(Article).count()
        assert count_after == count_before  # count unchanged
