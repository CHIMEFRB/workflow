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
        transferred_count (int): Number of works deposited to results.
    """
    transferred_count: int = 0
    if len(works) == 0:
        return transferred_count
    results_deposit_status = results.deposit(works)
    transferred_count = sum(results_deposit_status.values())
    if transferred_count == len(works):
        buckets.delete_ids([work["id"] for work in works])
    return transferred_count


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
    transfer_successful_work_count = deposit_work_to_results(
        buckets, results, successful_work
    )
    transfer_status["successful_work_transferred"] = transfer_successful_work_count

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
    transfer_failed_work_count = deposit_work_to_results(buckets, results, failed_work)
    transfer_status["failed_work_transferred"] = transfer_failed_work_count

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
    if len(stale_work) > 0:
        buckets.delete_ids([work["id"] for work in stale_work])
    transfer_status["stale_work_deleted"] = len(stale_work)
    return transfer_status


if __name__ == "__main__":
    transfer_work()
