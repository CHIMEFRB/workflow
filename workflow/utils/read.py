"""Read various workflow configurations."""

from pathlib import Path
from typing import Any

from requests import get
from requests.exceptions import RequestException
from yaml import safe_load

from workflow import MODULE_PATH
from workflow.utils.logger import get_logger

logger = get_logger("workflow.utils.read")


def workspace(source: str) -> Any:
    """Read a namespace YAML file.

    Args:
        source (str): Source of the namespace.
            Can be a URL, a file path, or a namespace name.

    Returns:
        Any: The namespace contents.
    """
    # Check if the source provided is a URL
    if source.startswith("http") or source.startswith("https"):
        logger.debug(f"source url: {source}")
        return url(source)

    # Check if the source provided is a valid file path
    if Path(source).exists():
        logger.debug(f"source path: {source}")
        return filename(source)

    for workspace in Path(MODULE_PATH, "workflow", "workspaces").glob("*.y*ml"):
        if workspace.stem == source:
            logger.debug(f"source path: {workspace.as_posix()}")
            return filename(workspace.as_posix())

    logger.error(f"workspace: {source} does not exist.")
    raise ValueError(f"workspace {source} does not exist.")


def url(source: str) -> Any:
    """Read a URL.

    Args:
        source (str): The URL to read.

    Returns:
        Any: The URL JSON response.
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

    Returns:
        Any: The source contents.
    """
    try:
        with open(source) as stream:
            return safe_load(stream)
    except Exception as error:
        logger.exception(error)
        raise error
