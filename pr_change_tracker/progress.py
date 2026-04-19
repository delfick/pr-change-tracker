from typing import Self

import attrs
import structlog

type Logger = structlog.stdlib.BoundLogger


@attrs.frozen
class Progress:
    logger: Logger

    def with_bound_logger(self, **values: object) -> Self:
        return attrs.evolve(self, logger=self.logger.bind(**values))
