import logging

import structlog
from structlog.processors import CallsiteParameter
from structlog.stdlib import BoundLogger
from structlog.typing import Processor


class Logger:
    """
    A configurable logger class that integrates Python's logging module with `structlog` to provide
    a structured and flexible logging system.

    Instance variables::
        log_level (str): The logging level (default is "INFO").
    """

    def __init__(self, log_level: str = "INFO"):
        self.log_level = log_level

    @property
    def _get_processors(self) -> list[Processor]:
        return [
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_logger_name,
            structlog.dev.set_exc_info,
            structlog.processors.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.stdlib.ExtraAdder(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=False),
            structlog.processors.CallsiteParameterAdder(
                [
                    CallsiteParameter.FILENAME,
                    CallsiteParameter.FUNC_NAME,
                ],
            ),
            structlog.dev.ConsoleRenderer(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ]

    @staticmethod
    def _configure_structlog(processors: list[Processor]) -> None:
        structlog.configure(
            processors=processors,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )

    def _configure_logging(self) -> None:
        root_logger = logging.getLogger()
        handler = logging.StreamHandler()

        if hasattr(root_logger, "addHandler"):
            root_logger.addHandler(handler)

        root_logger.setLevel(self.log_level.upper())

    def setup_logging(self) -> BoundLogger:
        self._configure_structlog(self._get_processors)
        self._configure_logging()
        return structlog.get_logger()


structlog_logger = Logger()
logger = structlog_logger.setup_logging()
