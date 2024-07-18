"""Read various workflow configurations."""

import re
from pathlib import Path
from typing import Any, Dict, Union

from requests import get
from rich.text import Text
from yaml import safe_load

from workflow import DEFAULT_WORKSPACE_PATH, MODULE_PATH
from workflow.utils.logger import get_logger

logger = get_logger("workflow.utils.read")

localspaces = Path(DEFAULT_WORKSPACE_PATH).parent
localstems = [space.stem for space in localspaces.glob("*.y*ml")]
modulespaces = Path(MODULE_PATH, "workflow", "workspaces")
modulestems = [space.stem for space in modulespaces.glob("*.y*ml")]


def workspace(source: Union[str, Path]) -> Dict[str, Any]:
    """Read a workspace configuration from source.

    Args:
        source (Union[str, Path]): Source of the workspace.
            Can be a URL, a file path, or a namespace name.

    Raises:
        ValueError: If not a yaml file, source

    Returns:
        Dict[str, Any]: Workspace Configuration
    """
    if isinstance(source, str) and Path(source).exists():
        source = Path(source)

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
            logger.info(f"workspace @ {source}")
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
        return safe_load(response.text)
    except Exception as error:
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


def get_active_workspace() -> Text:
    """Returns a Text with info about the active workspace.

    Returns
    -------
    Text
        Text instance with info.
    """
    _workspace = "workspace"
    text = Text()
    if _workspace in localstems:
        for possibility in localspaces.glob(f"{_workspace}.y*ml"):
            config = workspace(possibility)
            text.append("Currently using ", style="green")
            text.append(f"{config['workspace']} ", style="blue")
            text.append("workspace.", style="green")
    elif _workspace in modulestems:
        for possibility in modulespaces.glob(f"{_workspace}.y*ml"):
            config = workspace(possibility)
            text.append("Currently using ", style="green")
            text.append(f"{config['workspace']} ", style="blue")
            text.append("workspace.", style="green")
    else:
        text.append("There is not active workspace", style="red")
    return text


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
