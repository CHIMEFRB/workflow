"""Workflow decorators."""
from typing import Any, Callable

from workflow import get_logger

logger = get_logger("workflow.utils.decorators")


def try_request(func: Callable[..., Any]) -> Callable[..., Any]:
    """Try / Except wrapper for requests.

    Args:
        func (Callable[..., Any]): The function to wrap.

    Returns:
        Callable[..., Any]: The wrapped function.
    """

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as error:
            logger.exception(error)
            raise error

    return wrapper
