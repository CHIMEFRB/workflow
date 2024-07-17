"""Workflow Transfer Daemon."""

import time
from typing import Any, Dict, List, Union

import click
from click_params import JSON, URL, FirstOf

from workflow import DEFAULT_WORKSPACE_PATH
from workflow.http.context import HTTPContext
from workflow.lifecycle import configure
from workflow.utils import read
from workflow.utils.logger import get_logger

logger = get_logger("workflow.daemons.transfer")


@click.command()
@click.option("--sleep", "-s", default=5, help="seconds between transfers.")
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
@click.option("--limit", default=50, help="works per transfer.")
@click.option(
    "--cutoff", default=60 * 60 * 24 * 7, help="cutoff time in seconds for stale work."
)
@click.option(
    "--test-mode",
    is_flag=True,
    default=False,
    help="Enable test mode to avoid while True loop",
)
@click.option("--log-level", default="INFO", help="logging level.")
def transfer(
    workspace: Union[str, Dict[Any, Any]],
    limit: int,
    cutoff: int,
    sleep: int,
    test_mode: bool,
    log_level: str,
) -> Dict[str, int]:
    """Transfer Work.

    Args:
        sleep (int): seconds to sleep between transfers.
        workspace (Union[str, Dict[Any, Any]]): workspace config.
        test_mode (bool): Enable test mode to avoid while True loop.
        limit (int): works to transfer per run.
        cutoff (int): cutoff time in seconds for stale work.

    Returns:
        Dict[str, Any]: _description_
    """
    if test_mode:
        log_level = "DEBUG"
    logger.setLevel(log_level)
    logger.info("Starting Transfer Daemon")
    logger.info(f"Test Mode : {test_mode}")
    logger.info(f"Sleep Time: {sleep}")
    logger.info(f"Workspace : {workspace}")
    logger.info(f"Limit/Tx  : {limit}")
    logger.info(f"Cutoff    : {cutoff} days")
    try:
        configure.workspace(workspace=workspace)
        archive: bool = (
            read.workspace(DEFAULT_WORKSPACE_PATH)
            .get("config", {})
            .get("archive", {})
            .get("results", True)
        )
        logger.info(f"Archive   : {'Enabled' if archive else 'Disabled'}")
        http: HTTPContext = HTTPContext(backends=["buckets", "results"])
        logger.info("HTTP Context Initialized")
        logger.info(f"HTTP Context: Buckets Backend @ {http.buckets.baseurl}")
        logger.info(f"HTTP Context: Results Backend @ {http.results.baseurl}")

        # Check if Buckets and Results backends are available
        assert http.buckets.info(), "Buckets backend not available, exiting."
        assert http.results.info(), "Results backend not available, exiting."
    except Exception as error:
        logger.error(f"Transfer Initialization Error: {error}")
        exit(1)

    if test_mode:
        logger.debug("Running in Test Mode")
        outcome = perform(archive, limit, cutoff, http)
        logger.info(f"Transfer Outcome: {outcome}")
        return outcome
    else:
        iteration: int = 0
        while True:
            try:
                iteration += 1
                logger.debug(f"Transfer Iteration: {iteration}")
                outcome = perform(archive, limit, cutoff, http)
                logger.info(f"Transfer Outcome: {outcome}")
            except Exception as error:
                logger.error(f"Transfer Error: {error}")
            finally:
                time.sleep(sleep)


def check(payload: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Check payload for existing work in results backend.

    Args:
        payload (List[Dict[str, Any]]): list of work to check.

    Returns:
        List[Dict[str, Any]]: list of work that does not exist in results.
    """
    for data in payload:
        for key in ["products", "plots", "logs"]:
            if data["config"]["archive"][key] == "pass":
                data["config"]["archive"][key] = "bypass"
    return payload


def perform(
    archive: bool,
    limit: int,
    cutoff: int,
    http: HTTPContext,
) -> Dict[str, int]:
    """Perform transfer of work from Buckets to Results backend.

    Args:
        workspace (Union[str, Dict[Any, Any]]): workspace config.
        limit (int): works to transfer per run.
        cutoff (int): cutoff time in seconds for stale work.

    Returns:
        Dict[str, int]: transfer outcome.
    """
    delete: List[str] = []
    transfer: List[str] = []
    payload: List[Dict[str, Any]] = []
    response: Dict[str, Any] = {}
    transfered: int = 0

    # Find successful work in buckets
    logger.debug("checking successful work in buckets")
    for work in http.buckets.view(
        query={"status": "success"},
        projection={"id": True, "config": True},
        skip=0,
        limit=limit,
    ):
        if work["config"]["archive"]["results"] is False:
            delete.append(work["id"])
        elif work["config"]["archive"]["results"] is True and archive:
            transfer.append(work["id"])
        else:
            delete.append(work["id"])
    logger.debug(
        f"discovered {len(transfer)} transfer and {len(delete)} works to delete"
    )

    # Find failed work in buckets that is not retryable
    logger.debug("checking failed work in buckets")
    for work in http.buckets.view(
        query={
            "status": "failure",
            "$expr": {"$gte": ["$attempt", "$retries"]},
            "creation": {"$gt": time.time() - cutoff},
        },
        projection={"id": True, "config": True},
        skip=0,
        limit=limit,
    ):
        if work["config"]["archive"]["results"] is False:
            delete.append(work["id"])
        elif work["config"]["archive"]["results"] is True and archive:
            transfer.append(work["id"])
        else:
            delete.append(work["id"])
    logger.debug(
        f"discovered {len(transfer)} transfer and {len(delete)} works to delete"
    )

    # Find work in buckets that is too old and stale
    logger.debug("checking stale work in buckets")
    for work in http.buckets.view(
        query={
            "creation": {"$lt": time.time() - cutoff},
        },
        projection={"id": True},
        skip=0,
        limit=limit,
    ):
        delete.append(work["id"])
    logger.debug(
        f"discovered {len(transfer)} transfer and {len(delete)} works to delete"
    )

    # Transfer work to results
    payload = http.buckets.view(
        query={"id": {"$in": transfer}}, projection={}, skip=0, limit=limit * 3
    )
    payload = check(payload)
    try:
        logger.debug(f"tx {len(payload)} works to results")
        response = http.results.deposit(payload)
        logger.debug(f"tx {len(payload)} works to results successfully")
        logger.debug(f"tx response: {response}")
        delete = delete + transfer
        transfered = len(payload)
    except Exception as error:
        logger.warning(f"bulk transfer to results failed: {error}")
        logger.warning("checking for existing works in results")
        index: int = 0
        while index < len(payload):
            work = payload[index]
            if http.results.count(pipeline=work["pipeline"], query={"id": work["id"]}):
                delete.append(work["id"])
                logger.info(f"work {work['id']} already exists in results")
                payload.pop(index)
            else:
                index += 1
        logger.debug(f"retrying transfer of {len(payload)} works to results")
        response = http.results.deposit(payload)
        logger.info(
            f"transferred {len(payload)} works to results after duplicate check"
        )
        logger.debug(f"response: {response}")
        delete = delete + [work["id"] for work in payload]
        transfered = len(payload)

    if delete:
        logger.info(f"deleting {len(delete)} works from buckets")
        http.buckets.delete_ids(delete)
    logger.info(f"transferred {transfered}, deleted {len(delete)} works")
    return {
        "transfered": transfered,
        "deleted": len(delete),
    }


if __name__ == "__main__":
    transfer.main(args=["--test-mode=True", "--log-level=DEBUG"], standalone_mode=False)
