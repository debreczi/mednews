from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from .config import settings


engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)


# Enable WAL mode and foreign keys for every connection
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, _):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables and FTS5 virtual table."""
    from . import models  # noqa: F401 — ensures models are registered

    Base.metadata.create_all(bind=engine)

    # Create FTS5 virtual table and sync triggers
    with engine.connect() as conn:
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

        # Triggers to keep FTS in sync with articles table
        for trigger in [
            """CREATE TRIGGER IF NOT EXISTS articles_ai AFTER INSERT ON articles BEGIN
                INSERT INTO articles_fts(rowid, original_title, mednews_title, summary)
                VALUES (new.id, new.original_title, new.mednews_title, new.summary);
            END""",
            """CREATE TRIGGER IF NOT EXISTS articles_au AFTER UPDATE ON articles BEGIN
                INSERT INTO articles_fts(articles_fts, rowid, original_title, mednews_title, summary)
                VALUES ('delete', old.id, old.original_title, old.mednews_title, old.summary);
                INSERT INTO articles_fts(rowid, original_title, mednews_title, summary)
                VALUES (new.id, new.original_title, new.mednews_title, new.summary);
            END""",
            """CREATE TRIGGER IF NOT EXISTS articles_ad AFTER DELETE ON articles BEGIN
                INSERT INTO articles_fts(articles_fts, rowid, original_title, mednews_title, summary)
                VALUES ('delete', old.id, old.original_title, old.mednews_title, old.summary);
            END""",
        ]:
            conn.execute(text(trigger))

        # Rebuild FTS index on startup to ensure consistency
        conn.execute(text("INSERT INTO articles_fts(articles_fts) VALUES('rebuild')"))
        conn.commit()
