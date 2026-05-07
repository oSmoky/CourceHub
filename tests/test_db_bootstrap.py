from types import SimpleNamespace

from scripts import db_bootstrap


class NonSqliteEngine:
    dialect = SimpleNamespace(name="postgresql")

    def begin(self):
        raise AssertionError("SQLite-only repair should not run for PostgreSQL")


class FakeDb:
    engine = NonSqliteEngine()

    def __init__(self):
        self.created = False

    def create_all(self):
        self.created = True


def test_create_or_update_schema_skips_sqlite_repairs_for_postgresql(monkeypatch):
    fake_db = FakeDb()
    monkeypatch.setattr(db_bootstrap, "db", fake_db)

    db_bootstrap.create_or_update_schema()

    assert fake_db.created
