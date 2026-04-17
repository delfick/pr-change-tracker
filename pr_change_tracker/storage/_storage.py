import abc

import attrs
from sqlalchemy.ext.asyncio import AsyncEngine


class CommonStorage(abc.ABC):
    pass


@attrs.frozen
class PostgresStorage(CommonStorage):
    _engine: AsyncEngine
