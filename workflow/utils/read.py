"""Read various workflow configurations."""

import re
from pathlib import Path
from typing import Any, Dict

from requests import get
from requests.exceptions import RequestException
from yaml import safe_load

from workflow.utils.logger import get_logger

logger = get_logger("workflow.utils.read")


def workspace(source: str | Path) -> Dict[str, Any]:
    """Read a namespace YAML file.

    Args:
        source (str | Path): Source of the workspace.
            Can be a URL, a file path, or a namespace name.

    Returns:
        Any: The namespace contents.
    """
    if isinstance(source, Path):
        if source.exists():
            if source.suffix in [".yaml", ".yml"]:
                logger.debug(f"workspace @ {source.as_posix()}")
                return filename(source.as_posix())
            else:
                msg = f"{source} is not a valid yaml file."
                logger.error(msg)
                raise ValueError(msg)

    if isinstance(source, str):
        if is_valid_url(source):
            logger.debug(f"workspace @ {source}")
            return url(source)

    logger.error(f"workspace: {source} does not exist.")
    raise ValueError(f"workspace {source} does not exist.")


def url(source: str) -> Any:
    """Read a source URL.

    Args:
        source (str): The URL to read.

    Raises:
        error: If the request fails.

    Returns:
        Any: The source contents.
    """
    try:
        response = get(source)
        response.raise_for_status()
        return response.json()
    except RequestException as error:
        logger.exception(error)
        raise error


def filename(source: str) -> Any:
    """Read a source filename.

    Args:
        source (str): The filename to read.

    Raises:
        error: If the file cannot be read.

    Returns:
        Any: The source contents.
    """
    try:
        with open(source) as stream:
            return safe_load(stream)
    except Exception as error:
        logger.exception(error)
        raise error


def is_valid_url(url: str) -> bool:
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
