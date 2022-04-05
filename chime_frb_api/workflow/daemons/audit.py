from chime_frb_api.modules.buckets import Buckets

def audit_work(limit_per_run=1000):
    """Audit the Buckets DB for work that is failed, expired, or stale work.
    """

    buckets = Buckets() # any args?

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
        
    buckets.delete_ids(failed_work)

if __name__ == "__main__":
    audit_work()