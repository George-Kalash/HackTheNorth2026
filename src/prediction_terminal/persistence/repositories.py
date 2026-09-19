from datetime import timedelta

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from prediction_terminal.domain.markets import utcnow

from .tables import TABLES


class SQLRepository:
    def __init__(self, engine):
        self.engine = engine

    def get(self, table, id):
        t = TABLES[table]
        with self.engine.connect() as c:
            return c.execute(select(t.c.payload).where(t.c.id == id)).scalar_one_or_none()

    def list(self, table, limit=100, offset=0):
        t = TABLES[table]
        with self.engine.connect() as c:
            return list(
                c.execute(
                    select(t.c.payload).order_by(t.c.updated_at.desc(), t.c.id).limit(limit).offset(offset)
                ).scalars()
            )

    def put(self, table, id, payload, **keys):
        t = TABLES[table]
        insert = sqlite_insert if self.engine.dialect.name == "sqlite" else pg_insert
        values = {"id": id, "payload": payload, "updated_at": utcnow(), **keys}
        stmt = insert(t).values(**values).on_conflict_do_update(index_elements=["id"], set_=values)
        with self.engine.begin() as c:
            c.execute(stmt)

    def delete(self, table, id):
        t = TABLES[table]
        with self.engine.begin() as c:
            c.execute(delete(t).where(t.c.id == id))

    def latest_book(self, market_id):
        t = TABLES["book_snapshots"]
        with self.engine.connect() as c:
            return c.execute(
                select(t.c.payload).where(t.c.market_id == market_id).order_by(t.c.updated_at.desc()).limit(1)
            ).scalar_one_or_none()

    def prune(self, days):
        cutoff = utcnow() - timedelta(days=days)
        with self.engine.begin() as c:
            for name in ["book_snapshots", "price_points", "raw_inputs", "opportunity_snapshots"]:
                t = TABLES[name]
                c.execute(delete(t).where(t.c.updated_at < cutoff))
