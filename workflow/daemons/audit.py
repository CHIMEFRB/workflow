"""Audit Daemon."""
import time
from typing import Any, Dict, Optional

import click

from workflow.http.buckets import Buckets


@click.command()
@click.option(
    "--sleep",
    "-s",
    default=5,
    type=click.INT,
    help="Number of seconds to sleep between audits.",
)
@click.option(
    "--baseurl",
    "-b",
    type=click.STRING,
    default="http://frb-vsop.chime:8004",
    help="Buckets backend.",
)
@click.option(
    "--token",
    "-t",
    default=None,
    type=click.STRING,
    help="Authentication token.",
)
@click.option(
    "--test-mode",
    default=False,
    is_flag=True,
    type=click.BOOL,
    help="Enable test mode to avoid while True loop",
)
def workflow(
    sleep: int, baseurl: str, token: Optional[str], test_mode: bool
) -> Dict[str, Any]:
    """Audit for Buckets Database to find failed, expired, or stale work.

    Args:
        sleep (int): number of seconds to sleep between audits
        baseurl (str): location of the Buckets backend
        token (Optional[str]): authentication token
        test_mode (bool): enable test mode to avoid while True loop

    Returns:
        Dict[str, Any]: Audit results.
    """
    buckets: Buckets = Buckets(baseurl=baseurl, token=token)  # type: ignore
    if test_mode:
        return buckets.audit()
    while True:
        print(buckets.audit())
        time.sleep(sleep)


if __name__ == "__main__":
    workflow()
