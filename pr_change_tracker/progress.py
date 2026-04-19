import abc
from typing import Self

import attrs
import structlog

type Logger = structlog.stdlib.BoundLogger


class Metrics(abc.ABC):
    @abc.abstractmethod
    def increment(self, key: str) -> None: ...


class NoopMetrics(Metrics):
    """
    More just proving the point of being able to pass around metrics than actually implementing that
    """

    def increment(self, key: str) -> None:
        pass


@attrs.frozen
class Progress:
    logger: Logger
    metrics: Metrics = attrs.field(factory=NoopMetrics)

    def with_bound_logger(self, **values: object) -> Self:
        return attrs.evolve(self, logger=self.logger.bind(**values))
