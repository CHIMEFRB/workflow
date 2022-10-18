"""Transfer Daemon."""
import time
from typing import Any, Dict, List

import click

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
    try:
        transfer_status = False
        results_deposit_status = results.deposit(works)
        if all(results_deposit_status.values()):
            buckets.delete_ids([work["id"] for work in works])
            transfer_status = True
        return transfer_status
    except Exception as error:
        print(f"Exception occurred: {error}")
        transfer_status = False
        work_to_deposit = [work for work in works if is_work_already_deposited(results, work) is False]
        results_deposit_status = results.deposit(work_to_deposit)
        if all(results_deposit_status.values()) or results_deposit_status == {}:
            buckets.delete_ids([work["id"] for work in works])
            transfer_status = True
        return transfer_status


def is_work_already_deposited(results: Results, work: Dict[str, Any]) -> bool:
    """Check if a work has already been deposited to results.

    Args:
        results (Results): Results module.
        work (Dict[str, Any]): work to check 

    Returns:
        bool: _description_
    """
    return results.count(
        pipeline=work['pipeline'],
        query={'id': work['id']}
    ) == 1


@click.command()
@click.option("--sleep", "-s", default=5, help="Time to sleep between transfers")
@click.option(
    "--buckets-base-url",
    "-b",
    default="http://frb-vsop.chime:8004",
    help="Location of the Buckets backend.",
)
@click.option(
    "--results-base-url",
    "-r",
    default="http://frb-vsop.chime:8005",
    help="Location of the Results backend.",
)
@click.option(
    "--test-mode", default=False, help="Enable test mode to avoid while True loop"
)
def transfer_work(
    sleep: int,
    buckets_base_url: str,
    results_base_url: str,
    test_mode: bool,
    limit_per_run: int = 50,
) -> Dict[str, Any]:
    """Transfer successful Work from Buckets DB to Results DB.

    Args:
        sleep (int): number of seconds to sleep between transfers
        buckets_base_url (str): location of the Buckets backend
        results_base_url (str): location of the Results backend
        limit_per_run (int): Max number of failed Work entires to transfer per
        run of daemon.
    """

    def transfer(test_flag):
        buckets = Buckets(base_url=buckets_base_url, debug=test_mode)
        results = Results(base_url=results_base_url, debug=test_mode)
        transfer_status = {}
        # 1. Transfer successful Work
        # TODO: decide projection fields
        successful_work = buckets.view(
            query={"status": "success"},
            projection={},
            skip=0,
            limit=limit_per_run,
        )
        successful_work_to_delete = [
            work for work in successful_work if work["archive"] is False
        ]
        successful_work_to_transfer = [
            work for work in successful_work if work["archive"] is True
        ]
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
        failed_work_to_delete = [
            work for work in failed_work if work["archive"] is False
        ]
        failed_work_to_transfer = [
            work for work in failed_work if work["archive"] is True
        ]

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
        if test_flag:
            return transfer_status
        else:
            print(transfer_status)

    if test_mode:
        return transfer(test_flag=True)
    while True:
        transfer(test_flag=False)
        time.sleep(sleep)


if __name__ == "__main__":
    transfer_work()
