"""Workflow Python Logging Module."""

import logging
from datetime import datetime
from typing import Optional

import click
from rich.logging import RichHandler


def get_logger(name: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """Create a python logger with rich logging handler.

    Args:
        name (Optional[str], optional): Name of the module. Defaults to None.
        level (int, optional): . Defaults to logging.INFO.

    Returns:
        logging.Logger: Python logger object.
    """
    name = f"chimefrb.{name}" if name else "chimefrb"
    log = logging.getLogger(name=name)
    # Create timezone string
    tz = datetime.now().astimezone().tzinfo
    # # Detailed message format with level, module, line number, and and message
    format = "%(tag)s %(name)s %(message)s"
    logging.basicConfig(
        level=level,
        format=format,
        datefmt=f"%d %b %Y %H:%M:%S {tz}",
        handlers=[
            RichHandler(
                level=level,
                show_path=False,
                show_time=True,
                omit_repeated_times=False,
                markup=True,
                log_time_format=f"%d %b %Y %H:%M:%S {tz}",
                show_level=True,
                rich_tracebacks=True,
                tracebacks_suppress=[click],
                tracebacks_show_locals=True,
            )
        ],
        force=True,
    )
    for handler in logging.root.handlers:
        handler.addFilter(TagFilter(tag=""))
    return log


class TagFilter(logging.Filter):
    """Filter log messages by tag."""

    def __init__(self, tag: str) -> None:
        """Initialize the tag.

        Args:
            tag (str): tag.
        """
        self.tag = tag

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter log messages by tag.

        Args:
            record (logging.LogRecord): Log record.

        Returns:
            bool: True if the tag matches the log record.
        """
        record.tag = self.tag
        return True


def set_tag(tag: str) -> None:
    """Set the tag for the logger.

    Args:
        tag (str): tag.
    """
    for handler in logging.root.handlers:
        for filter in handler.filters:
            if isinstance(filter, TagFilter):
                filter.tag = tag


def unset_tag() -> None:
    """Unset the tag for the logger."""
    for handler in logging.root.handlers:
        for filter in handler.filters:
            if isinstance(filter, TagFilter):
                filter.tag = ""
