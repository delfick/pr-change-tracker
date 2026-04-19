from __future__ import annotations

import logging

import structlog

from pr_change_tracker import progress


def setup_logging(dev_logging: bool) -> progress.Logger:
    timestamper = structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S")
    shared_processors: list[structlog.typing.Processor] = [
        # structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        # structlog.processors.StackInfoRenderer(),
        timestamper,
    ]

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    log = structlog.get_logger().bind()
    assert isinstance(log, structlog.stdlib.BoundLogger)

    # And make stdlib logging use structlog
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            *(
                (structlog.dev.ConsoleRenderer(),)
                if dev_logging
                else (structlog.processors.JSONRenderer(),)
            ),
        ],
    )
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.propagate = False
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)

    return log
