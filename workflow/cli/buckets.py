"""Common Workflow Utilities."""

from typing import Any, Dict, List, Optional, Tuple

import click
from rich import pretty
from rich.console import Console
from rich.table import Table

from workflow.http.context import HTTPContext

pretty.install()
console = Console()


table = Table(
    title="\nWorkflow",
    show_header=True,
    header_style="magenta",
    title_style="bold magenta",
)


@click.group(name="buckets", help="Manage Workflow Buckets.")
def buckets():
    """Manage Workflow Buckets."""
    pass


@buckets.command("rm", help="Remove work from a bucket.")
@click.argument("bucket", type=str, required=True)
@click.option("-s", "--status", type=str, required=False, help="Filter by status.")
@click.option(
    "-e", "--event", type=int, required=False, multiple=True, help="Filter by event."
)
@click.option(
    "-t", "--tag", type=str, required=False, multiple=True, help="Filter by tag."
)
@click.option("-p", "--parent", type=str, required=False, help="Filter by parent.")
@click.option("-f", "--force", is_flag=True, help="Do not prompt for confirmation")
def remove(
    bucket: str,
    status: Optional[str] = None,
    event: Optional[Tuple[int]] = None,
    tag: Optional[Tuple[str]] = None,
    parent: Optional[str] = None,
    force: bool = False,
):
    """Remove work[s] from the buckets.

    Args:
        bucket (str): Name of the bucket.
        status (Optional[str], optional): Status of work. Defaults to None.
        event (Optional[Tuple[int]], optional): Filter by event. Defaults to None.
        tag (Optional[Tuple[str]], optional): Filter by tag. Defaults to None.
        parent (Optional[str], optional): Filter by parent. Defaults to None.
        force (bool, optional): Do not prompt for confirmation. Defaults to False.
    """
    http = HTTPContext()
    events: Optional[List[int]] = None
    tags: Optional[List[str]] = None
    if event:
        events = list(event)
    if tag:
        tags = list(tag)
    http.buckets.delete_many(
        pipeline=bucket,
        status=status,
        events=events,
        tags=tags,
        parent=parent,
        force=force,
    )


@buckets.command("ls")
@click.option("-d", "--details", is_flag=True, help="List details.")
def ls(details: bool = False):
    """List Buckets."""
    http = HTTPContext()
    if details:
        for key in ["name", "total", "queued", "running", "success", "failure"]:
            table.add_column(key, justify="right")
        pipelines = http.buckets.pipelines()
        for pipeline in pipelines:
            info = http.buckets.status(pipeline=pipeline)
            row = create_row(info)
            table.add_row(pipeline, *row)
    else:
        pipelines = http.buckets.pipelines()
        table.add_column("Buckets", max_width=50, justify="left")
        for pipeline in pipelines:
            table.add_row(pipeline)
    console.print(table)


@buckets.command("ps", help="List work in a bucket.")
@click.argument("bucket", type=str, required=True, default=None)
@click.option("-c", "--count", type=int, default=1, help="Number of works to list.")
def ps(bucket: str, count: int):
    """List work in the bucket.

    Args:
        bucket (str): Name of the bucket.
        count (int): Number of works to list.
    """
    http = HTTPContext()
    work = http.buckets.view(query={"pipeline": bucket}, projection={}, limit=count)
    console.print(work)


def create_row(details: Dict[str, Any]) -> List[str]:
    """Create a row of data for the table.

    Args:
        details (Dict[str, Any]): Details of the bucket.

    Returns:
        List[str]: List of values.
    """
    row_data: List[str] = []
    for value in details.values():
        row_data.append(str(value))
    return row_data
