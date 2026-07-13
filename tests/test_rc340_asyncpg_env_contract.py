from pathlib import Path


def test_rc340_database_url_uses_asyncpg():
    text = Path(
        "config/production.env.example"
    ).read_text(encoding="utf-8")

    assert (
        "DATABASE_URL=postgresql+asyncpg://"
        in text
    )
    assert "postgresql+psycopg://" not in text
