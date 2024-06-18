"""Results CLI Interface."""

from json import dumps
from typing import Any, Dict, Tuple

import click
from rich import pretty
from rich.console import Console
from rich.json import JSON
from rich.table import Table

from workflow.http.context import HTTPContext

pretty.install()
console = Console()


table = Table(
    title="\nWorkflow Results",
    show_header=True,
    header_style="magenta",
    title_style="bold magenta",
)
status_colors = {
    "success": "green",
    "failure": "red",
}
yes_no_colors = {"yes": "green", "no": "red"}


@click.group(name="results", help="Manage Workflow Results.")
def results():
    """Manage Workflow Results."""
    pass


@results.command("version", help="Show the version.")
def version():
    """Show the version."""
    http = HTTPContext(backends=["results"])
    console.print(http.results.info())


@results.command("count", help="Count of results per pipeline.")
def count():
    """Count pipelines on results backend."""
    http = HTTPContext(backends=["results"])
    count_result = http.results.status()
    table.add_column("Pipeline", max_width=50, justify="left", style="bright_blue")
    table.add_column("Count", max_width=50, justify="left")
    for pipeline, count in count_result.items():
        table.add_row(pipeline, str(count))
    console.print(table)


@results.command("view", help="View a set of filtered Results.")
@click.argument("pipeline", type=str, required=True)
@click.option(
    "--status",
    type=str,
    multiple=True,
    required=False,
    default=None,
    show_default=True,
    help="Filter by status.",
)
@click.option(
    "--event",
    type=int,
    multiple=True,
    required=False,
    default=None,
    show_default=True,
    help="Filter by event.",
)
@click.option(
    "--tags",
    type=str,
    multiple=True,
    required=False,
    default=None,
    show_default=True,
    help="Filter by tags.",
)
@click.option(
    "--limit",
    type=int,
    default=10,
    show_default=True,
    required=False,
    help="Number of results to view.",
)
@click.option(
    "--skip",
    type=int,
    default=0,
    show_default=True,
    required=False,
    help="Number of results to skip.",
)
@click.option(
    "--details",
    is_flag=True,
    default=False,
    show_default=True,
    required=False,
    help="Show detailed information.",
)
@click.option(
    "--json",
    is_flag=True,
    default=False,
    show_default=True,
    required=False,
    help="Output as JSON.",
)
def view(
    pipeline: str,
    status: Tuple[str],
    event: Tuple[int],
    tags: Tuple[str],
    skip: int = 0,
    limit: int = 10,
    details: bool = False,
    json: bool = False,
):
    """View a set of filtered Results."""
    http = HTTPContext()
    if details:
        projection = {}
    else:
        projection = {
            "id": True,
            "results": True,
            "products": True,
            "plots": True,
            "status": True,
        }
    query: Dict[str, Any] = {}
    if status:
        query["status"] = {"$in": list(status)}
    if event:
        query["event"] = {"$in": list(event)}
    if tags:
        query["tags"] = {"$in": list(tags)}

    results = http.results.view(
        pipeline=pipeline, query=query, projection=projection, skip=skip, limit=limit
    )

    if json:
        console.print(JSON(dumps(results), indent=2))
        return

    if not results:
        console.print("No results found.")
        return
    from typing import List

    values: List[JSON] = []
    for name in results[0].keys():
        table.add_column(name, justify="left", style="bright_blue")
    for result in results:
        for value in result.values():
            values.append(JSON(dumps(value), indent=1))
    table.add_row(*values)
    console.print(table)
    return
