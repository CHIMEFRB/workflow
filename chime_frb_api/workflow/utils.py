"""Common Workflow Utilities."""
from typing import Any, Dict, List, Optional

import click
from rich import pretty, print
from rich.console import Console
from rich.table import Table

from chime_frb_api.modules.buckets import Buckets

pretty.install()
console = Console()
table = Table(
    title="\nWorkflow Buckets",
    show_header=True,
    header_style="magenta",
    title_style="bold magenta",
)


@click.group(name="buckets", help="Manage workflow buckets.")
def buckets():
    """Manage workflow pipelines."""
    pass


@buckets.command("prune", help="Prune work[s] from a workflow bucket.")
@click.option("name", "--name", type=str, required=True, help="Name of the bucket.")
@click.option("event", "--event", type=int, required=False, help="CHIME/FRB Event ID.")
@click.option(
    "status",
    "--status",
    type=str,
    required=False,
    help="To prune work of particular status.",
)
def prune_work(name: str, event: Optional[int] = None, status: Optional[str] = None):
    """Prune work[s] from the workflow backend.

    Args:
        name (str): Name of the workflow pipeline.
        event (Optional[int], optional): CHIME/FRB Event ID. Defaults to None.
        status (Optional[str], optional): Status of work[s] to prune. Defaults to None.
    """
    events: Optional[List[int]] = None
    if event is not None:
        events = [event]
    buckets = Buckets()
    buckets.delete_many(pipeline=name, status=status, events=events)


@buckets.command("ls", help="List all active buckets.")
def ls():
    """List all active buckets."""
    buckets = Buckets()
    pipelines = buckets.pipelines()
    table.add_column("Active Pipelines", max_width=50, justify="left")
    for pipeline in pipelines:
        table.add_row(pipeline)
    console.print(table)


@buckets.command("details", help="List the detail of buckets[s].")
@click.option("all", "-a", "--all", is_flag=True, help="List details of all buckets.")
@click.argument("name", type=str, required=False, default=None)
def details(name: Optional[str] = None, all: bool = False):
    """List the details of the bucket[s].

    Args:
        name (Optional[str], optional): Name of the bucket. Defaults to None.
        all (bool, optional): Whether to show all buckets. Defaults to False.
    """
    buckets = Buckets()
    details = buckets.status(pipeline=None)
    table.add_column("name", justify="left")
    for key in details.keys():
        table.add_column(key, justify="right")
    table.add_row("total", *create_row(details))
    if all:
        pipelines = buckets.pipelines()
        for pipeline in pipelines:
            details = buckets.status(pipeline=pipeline)
            row = create_row(details)
            table.add_row(pipeline, *row)
    elif name:
        details = buckets.status(pipeline=name)
        row = create_row(details)
        table.add_row(name, *row)
    console.print(table)


@buckets.command("view", help="View work in a bucket.")
@click.argument("name", type=str, required=True)
@click.option(
    "count",
    "-c",
    "--count",
    type=int,
    required=False,
    default=3,
    help="Number of work to show.",
)
def view(name: str, count: int = 3):
    """View work in a bucket.

    Args:
        name (str): Name of the bucket.
        count (int, optional): Number of work to show. Defaults to 3.
    """
    buckets = Buckets()
    work = buckets.view(query={"pipeline": name}, projection={}, limit=count)
    print(work)


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
