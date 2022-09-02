"""Transfer Daemon."""
import time
import click
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

@click.command()
@click.option("--sleep", "-s", default=5, help="Time to sleep between transfers")
@click.option("--buckets-base-url", "-b", default="http://frb-vsop.chime:8004", help="Location of the Buckets backend.")
@click.option("--results-base-url", "-r", default="http://frb-vsop.chime:8005", help="Location of the Results backend.")
def transfer_work(
    sleep: int,
    buckets_base_url: str,
    results_base_url: str,
    limit_per_run: int = 81,
) -> Dict[str, Any]:
    """Transfer successful Work from Buckets DB to Results DB.

    Args:
        sleep (int): number of seconds to sleep between transfers
        buckets_base_url (str): location of the Buckets backend
        results_base_url (str): location of the Results backend
        limit_per_run (int): Max number of failed Work entires to transfer per
        run of daemon.
    """
    buckets_kwargs = {"base_url": buckets_base_url}
    results_kwargs = {"base_url": results_base_url}
    while True:
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
        successful_work_to_delete = [work for work in successful_work if work['archive'] is False]
        successful_work_to_transfer = [work for work in successful_work if work['archive'] is True]
        if successful_work_to_transfer:
            transfer_status["successful_work_transferred"] = deposit_work_to_results(
                buckets, results, successful_work_to_transfer
            )
        if successful_work_to_delete:
            buckets.delete_ids([work["id"] for work in successful_work_to_delete])
            transfer_status["successful_work_deleted"] = True

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
        failed_work_to_delete = [work for work in failed_work if work['archive'] is False]
        failed_work_to_transfer = [work for work in failed_work if work['archive'] is True]

        if failed_work_to_transfer:
            transfer_status["failed_work_transferred"] = deposit_work_to_results(
                buckets, results, failed_work_to_transfer
            )
        if failed_work_to_delete:
            buckets.delete_ids([work["id"] for work in failed_work_to_delete])
            transfer_status["failed_work_deleted"] = True

        # 3. Delete stale Work (cut off time: 7 days)
        cutoff_creation_time = time.time() - (60 * 60 * 24 * 7)
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
        
        print(transfer_status)
        time.sleep(sleep)


if __name__ == "__main__":
    transfer_work()
