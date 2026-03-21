import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.main import app
from backend.database import Base, get_db


def _make_engine():
    """Create a fresh in-memory SQLite engine with schema and FTS5 table."""
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # all sessions share the same single connection
    )
    Base.metadata.create_all(eng)
    with eng.connect() as conn:
        conn.execute(text("""
            CREATE VIRTUAL TABLE IF NOT EXISTS articles_fts
            USING fts5(
                original_title,
                mednews_title,
                summary,
                content='articles',
                content_rowid='id'
            )
        """))
        conn.commit()
    return eng


@pytest.fixture
def engine():
    """Fresh in-memory DB per test — guarantees isolation even with commits."""
    return _make_engine()


@pytest.fixture
def db(engine):
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def client(engine):
    Session = sessionmaker(bind=engine)

    def override_get_db():
        session = Session()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
