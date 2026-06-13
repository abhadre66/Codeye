import logging
import sys
import uuid
from contextvars import ContextVar

import structlog

from reviewmind.core.config import settings

_correlation_id: ContextVar[str] = ContextVar("correlation_id", default="-")


def bind_correlation_id(correlation_id: str | None = None) -> str:
    """Set (or generate) a correlation ID for the current async task."""
    cid = correlation_id or str(uuid.uuid4())
    _correlation_id.set(cid)
    return cid


def _add_correlation_id(logger, method_name, event_dict):
    event_dict["correlation_id"] = _correlation_id.get()
    return event_dict


def configure_logging() -> None:
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stderr,  # never stdout - would corrupt MCP stdio protocol
        level=settings.log_level,
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            _add_correlation_id,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(settings.log_level)
        ),
    )


def get_logger(name: str) -> structlog.BoundLogger:
    return structlog.get_logger(name)
