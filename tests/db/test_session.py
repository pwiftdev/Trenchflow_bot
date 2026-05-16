from db.session import async_database_url, sync_database_url


def test_async_database_url_from_postgresql() -> None:
    url = "postgresql://user:pass@host:5432/db"
    assert async_database_url(url) == "postgresql+asyncpg://user:pass@host:5432/db"


def test_sync_database_url_for_alembic() -> None:
    url = "postgresql+asyncpg://user:pass@host:5432/db"
    assert sync_database_url(url) == "postgresql+psycopg://user:pass@host:5432/db"
