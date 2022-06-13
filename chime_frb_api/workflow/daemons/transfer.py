"""Transfer Daemon."""
import time
from typing import Any, Dict, List

from chime_frb_api.modules.buckets import Buckets
from chime_frb_api.modules.results import Results


def deposit_work_to_results(
    buckets: Buckets, results: Results, works: List[Dict[str, Any]]
) -> int:
    """Deposit work to results, and remove them from buckets.

    Args:
        buckets (Buckets): Buckets module.
        results (Results): Results module.
        works (List[Dict[str, Any]]): Work to deposit.

    Returns:
        transfer_status (bool): Number of works deposited to results.
    """
    transfer_status = False
    results_deposit_status = results.deposit(works)
    if all(results_deposit_status.values()):
        buckets.delete_ids([work["id"] for work in works])
        transfer_status = True
    return transfer_status


def transfer_work(
    limit_per_run: int = 1000,
    buckets_kwargs: Dict[str, Any] = {},
    results_kwargs: Dict[str, Any] = {},
) -> Dict[str, Any]:
    """Transfer successful Work from Buckets DB to Results DB.

    Args:
        limit_per_run (int): Max number of failed Work entires to transfer per
        run of daemon.
        buckets_kwargs (Dict[str, Any]): Keyword arguments for the Buckets API.
        results_kwargs (Dict[str, Any]): Keyword arguments for the Results API.

    Returns:
        transfer_status (Dict[str, Any]): Transfer results.
    """
    buckets = Buckets(**buckets_kwargs)
    results = Results(**results_kwargs)
    transfer_status = {}
    # 1. Transfer successful Work
    # TODO: decide projection fields
    successful_work = buckets.view(
        query={"status": "success"},
        projection={},
        skip=0,
        limit=limit_per_run,
    )
    if successful_work:
        transfer_status["successful_work_transferred"] = deposit_work_to_results(
            buckets, results, successful_work
        )

    # 2. Transfer failed Work
    # TODO: decide projection fields
    failed_work = buckets.view(
        query={
            "status": "failure",
            "$expr": {"$gte": ["$attempt", "$retries"]},
        },
        projection={},
        skip=0,
        limit=limit_per_run,
    )
    if failed_work:
        transfer_status["failed_work_transferred"] = deposit_work_to_results(
            buckets, results, failed_work
        )

    # 3. Delete stale Work (cut off time: 14 days)
    cutoff_creation_time = time.time() - (60 * 60 * 24 * 14)
    stale_work = buckets.view(
        query={
            "status": "failure",
            "creation": {"$lt": cutoff_creation_time},
        },
        projection={},
        skip=0,
        limit=limit_per_run,
    )
    if stale_work:
        buckets.delete_ids([work["id"] for work in stale_work])
        transfer_status["stale_work_deleted"] = True
    return transfer_status


if __name__ == "__main__":
    transfer_work()
