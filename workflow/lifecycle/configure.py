"""Configure workflow during the lifecycle."""

from logging import Formatter, Logger
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import requests
from logging_loki import LokiHandler

from workflow import DEFAULT_WORKSPACE_PATH
from workflow.utils import read, validate, write
from workflow.utils.logger import get_logger

logger = get_logger("workflow.lifecycle.process")


def workspace(workspace: Union[str, Dict[Any, Any]]):
    """Configure the workspace during the lifecycle.

    Args:
        workspace (Union[str, Dict[Any, Any]]): Workspace configuration src.
    """
    # workspace passed as a string for Path or URL
    if isinstance(workspace, str):
        if Path(workspace).absolute().exists():
            if workspace == DEFAULT_WORKSPACE_PATH.as_posix():
                logger.info("Running with active workspace.")
            else:
                logger.info(f"Saving {workspace} as active workspace.")
                # Save the workspace path to the default location
                write.workspace(Path(workspace))
        # Check if the workspace is a URL
        elif validate.url(workspace):
            logger.info(f"Running with workspace from URL {workspace}")
            # Fetch the workspace from the URL
            payload = read.url(workspace)
            logger.info(f"URL Workspace: {payload}")
            # Save the workspace to the default location
            write.workspace(payload)

    if isinstance(workspace, dict):
        name: Optional[str] = workspace.get("workspace")
        logger.info(f"Running with dict workspace: {name}")
        # Save the workspace to the default location
        write.workspace(workspace)


def loki(logger: Logger, config: Dict[str, Any]) -> bool:
    """Add a Loki handler to the logger.

    Args:
        logger (Logger): Python logger
        config (Dict[str, Any]): Workspace configuration

    Returns:
        bool: Loki handler status
    """
    status: bool = False
    urls: List[str] = []
    loki_urls: Optional[Any] = config.get("http", {}).get("baseurls", {}).get("loki")
    loki_tags: Optional[Any] = config.get("logging", {}).get("loki", {}).get("tags", {})
    if not loki_urls:
        return status
    elif isinstance(loki_urls, str):
        urls = [loki_urls]
    elif isinstance(loki_urls, list):
        urls = loki_urls
    else:
        logger.error(f"Invalid Loki URL: {loki_urls}")
        return status

    for url in urls:
        try:
            status_code: int = requests.get(
                url.replace("loki/api/v1/push", "ready"), timeout=1
            ).status_code
            if status_code == 200:
                loki_handler = LokiHandler(url=url, tags=loki_tags, version="1")
                loki_handler.setFormatter(
                    Formatter("%(levelname)s %(tag)s %(name)s %(message)s")
                )
                loki_handler.setLevel(logger.root.level)
                logger.root.addHandler(loki_handler)
                logger.debug(f"Loki URL: {url}")
                status = True
                return status
        except Exception as error:
            logger.debug(error)
    return status
