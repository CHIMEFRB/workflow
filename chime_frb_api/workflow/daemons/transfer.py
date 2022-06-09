from chime_frb_api.modules.buckets import Buckets
from chime_frb_api.modules.results import Results
from time import time

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
    # 1. fetch all successful work from buckets
    # TODO: decide projection fields
    successful_work = buckets.view(
        query = {"status": "success"},
        projection = {},
        skip = 0, 
        limit = limit_per_run,
    )
    # 2. deposit successful work into results; delete them from buckets
    if len(successful_work) > 0:
        results_deposit_status = results.deposit(successful_work)
        if all(results_deposit_status.values()) == True:
            buckets.delete_ids([work["id"] for work in successful_work])
            return True
        else:
            # TODO: decide what to do if deposit fails
            return False
    # 3. fetch failed work (attempt >= retries) from buckets
    # TODO: decide projection fields
    failed_work = buckets.view(
        query = {
            "status": "failure",
            "$expr": {"$gte": ["attempt","retries"]},
        },
        projection = {},
        skip = 0,
        limit = limit_per_run,
    )
    # 4. deposit failed work into results; delete them from buckets
    if len(failed_work) > 0:
        results_deposit_status = results.deposit(failed_work)
        if all(results_deposit_status.values()) == True:
            buckets.delete_ids([work["id"] for work in failed_work])
            return True
        else:
            # TODO: decide what to do if deposit fails
            return False


if __name__ == "__main__":
    transfer_work()
