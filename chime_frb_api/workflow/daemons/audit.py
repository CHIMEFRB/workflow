from chime_frb_api.modules.buckets import Buckets

def audit_work(limit_per_run=1000,**kwargs):
    """Audit the Buckets DB for work that is failed, expired, or stale work.

    Args:
        limit_per_run (int): Max number of failed Work entires to delete per
        run of daemon.
        **kwargs (Dict[str, Any]): Keyword arguments for the Buckets API.
    """

    buckets = Buckets(**kwargs)

    # the buckets.audit call:
    # 1) failed: retries 'failure' work if attempts < retries 
    # 2) expired: fails 'running' work with run time > timeout
    # 3) stale: fails all work that is older than 31 days
    audit_results = buckets.audit()

    # then want to delete failed work that has used up retries
    failed_work = buckets.view(
        query = {
            "status": "failure",
            "$expr": {"$gte": ["attempt","retries"]},
        },
        projection = {"_id": True},
        skip = 0,
        limit = limit_per_run,
    )
    print(failed_work)
        
    audit_results["deleted"] = 0
    if len(failed_work) > 0:
        response = buckets.delete_ids(failed_work)
        print(response)
        if response == True:
            audit_results["deleted"] = len(failed_work)

    return audit_results

if __name__ == "__main__":
    audit_work()