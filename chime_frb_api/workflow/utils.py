"""Common Workflow Utilities."""
from typing import List, Optional

import click

from chime_frb_api.modules.buckets import Buckets


@click.command("prune", help="Prune work[s] from a workflow backend.")
@click.option("bucket", "--bucket", type=str, required=True, help="Name of the bucket.")
@click.option("event", "--event", type=int, required=False, help="CHIME/FRB Event ID.")
@click.option(
    "status", "--status", type=str, required=False, help="Status of the work."
)
def prune_work(bucket: str, event: Optional[int] = None, status: Optional[str] = None):
    """Prune work[s] from the workflow backend.

    Args:
        bucket (str): Name of the bucket.
        event (Optional[int], optional): CHIME/FRB Event ID. Defaults to None.
        status (Optional[str], optional): Status of work[s] to prune. Defaults to None.
    """
    events: Optional[List[int]] = None
    if event is not None:
        events = [event]
    buckets = Buckets()
    buckets.delete_many(pipeline=bucket, status=status, events=events)
