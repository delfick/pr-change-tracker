from __future__ import annotations

import sqlalchemy
import sqlalchemy.engine.url
from sqlalchemy import orm
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

type BigInt = int

registry = orm.registry(type_annotation_map={BigInt: sqlalchemy.BigInteger})


def make_engine(*, postgres_url: str) -> AsyncEngine:
    url = sqlalchemy.engine.url.make_url(postgres_url)
    url = url.set(drivername="postgresql+psycopg")
    return create_async_engine(url)
