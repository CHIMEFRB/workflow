"""Audit Daemon."""
from typing import Any, Dict

from chime_frb_api.modules.buckets import Buckets


def workflow(**kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """Audit the Buckets DB for work that is failed, expired, or stale work.

    Args:
        **kwargs (Dict[str, Any]): Keyword arguments for the Buckets API.
    """

    buckets: Buckets = Buckets(**kwargs)  # type: ignore
    return buckets.audit()


if __name__ == "__main__":
    workflow()
