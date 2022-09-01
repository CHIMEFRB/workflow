"""Audit Daemon."""
from typing import Any, Dict
import click
import time
from chime_frb_api.modules.buckets import Buckets

@click.command()
@click.option("--sleep", "-s", default=5, help="Time to sleep between audits")
@click.option("--base-url", "-b", default="http://frb-vsop.chime:8004", help="Location of the Buckets backend.")
def workflow(sleep:int, base_url: str) -> Dict[str, Any]:
    """Audit the Buckets DB for work that is failed, expired, or stale work.

    Args:
        sleep (int): number of seconds to sleep between audits
        base_url (str): location of the Buckets backend
    """
    kwargs = {"base_url": base_url}
    while True:
        buckets: Buckets = Buckets(**kwargs)
        print(buckets.audit())
        time.sleep(sleep)

if __name__ == "__main__":
    workflow()
