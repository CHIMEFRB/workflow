"""Utilities for validating data."""

import re


def url(url: str) -> bool:
    """Return True if the URL is valid.

    Args:
        url (str): The URL to validate.

    Returns:
        bool: True if the URL is valid.
    """
    regex = re.compile(
        r"^(https?://)?"  # http:// or https:// (optional)
        r"("
        r"localhost|"  # localhost
        r"((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"  # ipv4
        r"(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)"  # ipv4
        r"|"
        r"([a-zA-Z0-9]+([-.\w]*[a-zA-Z0-9])*"  # domain...
        r"(\.[a-zA-Z0-9]{2,3})+)"  # ...with top level domain
        r")"
        r"(?::\d{2,5})?"  # optional port
        r"(?:/?|[/?]\S+)?$",
        re.IGNORECASE,
    )  # optional trailing path/query

    return re.match(regex, url) is not None
