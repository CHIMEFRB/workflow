"""Common Workflow Utilities."""
from typing import Any, Dict, List, Optional

import click
from rich import pretty
from rich.console import Console
from rich.table import Table

from chime_frb_api.modules.buckets import Buckets

pretty.install()
console = Console()
table = Table(title="Workflow Status", show_header=True, header_style="bold magenta")


@click.group(name="pipeline", help="Manage workflow pipelines.")
def pipeline():
    """Manage workflow pipelines."""
    pass


@pipeline.command("prune", help="Prune work[s] from a workflow pipeline.")
@click.option("name", "--name", type=str, required=True, help="Name of the pipeline.")
@click.option("event", "--event", type=int, required=False, help="CHIME/FRB Event ID.")
@click.option(
    "status", "--status", type=str, required=False, help="Status of the work."
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


@pipeline.command("ls", help="List all active pipelines.")
def ls(details: bool = False):
    """List all available pipelines."""
    buckets = Buckets()
    pipelines = buckets.pipelines()
    table.add_column("Active Pipelines", max_width=50, justify="left")
    for pipeline in pipelines:
        table.add_row(pipeline)
    console.print(table)


@pipeline.command("details", help="List the details of pipeline[s].")
@click.option("all", "-a", "--all", is_flag=True, help="List details of all pipelines.")
@click.argument("name", type=str, required=False)
def details(name: Optional[str] = None, all: bool = False):
    """List the details of a pipeline."""
    buckets = Buckets()
    details = buckets.status(pipeline=name)
    table.add_column("", justify="left")
    tablify("total", details)
    if all:
        pipelines = buckets.pipelines()
        for pipeline in pipelines:
            details = buckets.status(pipeline=pipeline)
            tablify(pipeline, details)
    elif name:
        details = buckets.status(pipeline=name)
        tablify(name, details)
    console.print(table)


def tablify(name: str, details: Dict[str, Any]):
    """Format the details of a pipeline into a table.

    Args:
        name (str): Name of the pipeline.
        details (Dict[str, Any]): Details of the pipeline.
    """
    row = [name]
    for key, value in details.items():
        table.add_column(key, justify="right")
        row.append(str(value))
    table.add_row(*row)
