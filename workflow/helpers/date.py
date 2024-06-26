"""Helper functions for working with dates and times."""

from datetime import datetime
from typing import Dict


def get(format: str) -> Dict[str, str]:
    """Get the current date and time in the specified format.

    Args:
        format (str): The format to return the date and time in.

    Example:
        from workflow.helpers import date
        date.get("%Y-%m-%d %H:%M:%S")

    Returns:
        str: The current date and time.
    """
    date = datetime.now().strftime(format)
    results: Dict[str, str] = {"output": date}
    return results


def get_ctime() -> Dict[str, float]:
    """Get the current time in seconds since the epoch.

    Returns:
        float: The current time in seconds since the epoch.
    """
    ctime: float = datetime.now().timestamp()
    results: Dict[str, float] = {"output": ctime}
    return results
