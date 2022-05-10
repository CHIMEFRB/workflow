from chime_frb_api.modules.buckets import Buckets
from chime_frb_api.modules.results import Results

def transfer_work(limit_per_run=1000,buckets_kwargs={},results_kwargs={}):
    """Transfer successful Work from Buckets DB to Results DB

    Args:
        limit_per_run (int): Max number of failed Work entires to transfer per
        run of daemon.
        buckets_kwargs (Dict[str, Any]): Keyword arguments for the Buckets API.
        results_kwargs (Dict[str, Any]): Keyword arguments for the Buckets API.
    """
    buckets = Buckets(**buckets_kwargs)
    results = Results(**results_kwargs)

    successful_work = buckets.view(
        query = {"status": "success"},
        projection = {}, # do we want everything?
        skip = 0, 
        limit = limit_per_run,
    )

    if len(successful_work):
        status = results.deposit(successful_work)
        if all(status.values()) == True:
            buckets.delete_ids([work["id"] for work in successful_work])
            return True
        else:
            # what do we want to do if the results.deposit is not successful?
            return False

if __name__ == "__main__":
    transfer_work()
    

