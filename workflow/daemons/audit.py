"""Audit Daemon."""

import time
from typing import Any, Dict, Union

import click
from click_params import JSON, URL, FirstOf

from workflow import DEFAULT_WORKSPACE_PATH
from workflow.http.context import HTTPContext
from workflow.lifecycle import configure
from workflow.utils.logger import get_logger

logger = get_logger("workflow.daemons.audit")


@click.command()
@click.option(
    "--sleep",
    "-s",
    default=5,
    type=click.INT,
    help="Number of seconds to sleep between audits.",
)
@click.option(
    "-w",
    "--workspace",
    type=FirstOf(
        click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True),
        URL,
        JSON,
    ),
    default=(DEFAULT_WORKSPACE_PATH.as_posix()),
    show_default=True,
    help="workspace config.",
)
@click.option(
    "--test-mode",
    default=False,
    is_flag=True,
    type=click.BOOL,
    help="Enable test mode to avoid while True loop",
)
def audit(
    sleep: int,
    workspace: Union[str, Dict[Any, Any]],
    test_mode: bool,
) -> Dict[str, Any]:
    """Audit Buckets.

    Args:
        sleep (int): number of seconds to sleep between audits
        workspace (Union[str, Dict[Any, Any]]): workspace config
        token (Optional[str]): authentication token
        test_mode (bool): enable test mode to avoid while True loop

    Returns:
        Dict[str, Any]: Audit results.
    """
    logger.info("Starting Audit Daemon")
    logger.info(f"Sleep Time: {sleep}")
    logger.info(f"Workspace : {workspace}")
    logger.info(f"Test Mode : {test_mode}")
    configure.workspace(workspace=workspace)

    http: HTTPContext = HTTPContext(backends=["buckets"])
    logger.info("HTTP Context Initialized")
    logger.info(f"HTTP Context: Buckets Backend @ {http.buckets.baseurl}")
    if test_mode:
        return http.buckets.audit()
    while True:
        response = http.buckets.audit()
        logger.info(response)
        time.sleep(sleep)
