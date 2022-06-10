from chime_frb_api.modules.buckets import Buckets


def audit_work(**kwargs):
    """Audit the Buckets DB for work that is failed, expired, or stale work.

    Args:
        **kwargs (Dict[str, Any]): Keyword arguments for the Buckets API.
    """

    buckets = Buckets(**kwargs)
    return buckets.audit()

if __name__ == "__main__":
    audit_work()
