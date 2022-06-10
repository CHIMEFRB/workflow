from time import time

from chime_frb_api.modules.buckets import Buckets


def audit_work(limit_per_run=1000,**kwargs):
    """Audit the Buckets DB for work that is failed, expired, or stale work.

    Args:
        limit_per_run (int): Max number of failed Work entires to delete per
        run of daemon.
        **kwargs (Dict[str, Any]): Keyword arguments for the Buckets API.
    """

    buckets = Buckets(**kwargs)
    audit_results = buckets.audit()
    return audit_results

if __name__ == "__main__":
    audit_work()
