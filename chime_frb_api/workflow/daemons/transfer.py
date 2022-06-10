import time

from chime_frb_api.modules.buckets import Buckets
from chime_frb_api.modules.results import Results


def deposit_work_to_results(buckets, results, works):
    """Deposit work to results, and remove them from buckets

    Args:
        buckets (Buckets): Buckets module.
        results (Results): Results module.
        works (List[Dict[str, Any]]): Work to deposit.
    """
    if len(works) == 0:
        return True
    results_deposit_status = results.deposit(works)
    if all(results_deposit_status.values()) == True:
        buckets.delete_ids([work["id"] for work in works])
        return True
    return False

def transfer_work(limit_per_run=1000,buckets_kwargs={},results_kwargs={}):
    """Transfer successful Work from Buckets DB to Results DB

    Args:
        limit_per_run (int): Max number of failed Work entires to transfer per
        run of daemon.
        buckets_kwargs (Dict[str, Any]): Keyword arguments for the Buckets API.
        results_kwargs (Dict[str, Any]): Keyword arguments for the Results API.
    """
    buckets = Buckets(**buckets_kwargs)
    results = Results(**results_kwargs)
    # 1. Transfer successful Work
    # TODO: decide projection fields
    successful_work = buckets.view(
        query={"status": "success"},
        projection={},
        skip=0,
        limit=limit_per_run,
    )
    deposit_successful_work_status = deposit_work_to_results(buckets, results, successful_work)

    # 2. Transfer failed Work
    # TODO: decide projection fields
    failed_work = buckets.view(
        query={
            "status": "failure",
            "$expr": {"$gte": ["attempt","retries"]},
        },
        projection={},
        skip=0,
        limit=limit_per_run,
    )
    deposit_failed_work_status = deposit_work_to_results(buckets, results, failed_work)

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
    return deposit_successful_work_status and deposit_failed_work_status


if __name__ == "__main__":
    transfer_work()
