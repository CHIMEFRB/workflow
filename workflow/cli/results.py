"""Results CLI Interface."""

from json import dumps
from typing import Optional

import click
from rich import pretty
from rich.console import Console
from rich.json import JSON
from rich.table import Table
from rich.text import Text

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
    http = HTTPContext()
    console.print(http.results.info())


@results.command("count", help="Returns count of all pipelines on results backend.")
@click.option("--status", "-s", help="Count by status")
def count(status: Optional[str] = None):
    """Count pipelines on results backend."""
    http = HTTPContext()
    count_result = http.results.count()
    table.add_column("Pipeline", max_width=50, justify="left", style="bright_blue")
    table.add_column("Count", max_width=50, justify="left")
    for pipeline, count in count_result.items():
        table.add_row(pipeline, str(count))
    console.print(table)


@results.command("view", help="Returns Results from the specified pipeline.")
@click.argument("pipeline", type=str, required=True)
@click.option("status", "-s", type=str, required=False, help="Filter by status.")
@click.option("skip", "-k", type=int, required=False, help="Skip n results.")
@click.option(
    "limit", "-l", type=int, default=50, required=False, help="Deliver only n results."
)
def view(
    pipeline: str,
    status: Optional[str] = None,
    skip: Optional[int] = None,
    limit: Optional[int] = None,
):
    """View a set of filtered Results.

    Parameters
    ----------
    pipeline : str
        Pipeline name.
    status : Optional[str], optional
        Results status, by default None
    skip : Optional[int], optional
        Skip n results, by default None
    limit : Optional[int], optional
        Deliver n results, by default None
    """
    http = HTTPContext()
    payload = {
        "query": {"pipeline": pipeline},
        "projection": {
            "id": True,
            "pipeline": True,
            "products": True,
            "plots": True,
            "function": True,
            "command": True,
            "status": True,
        },
    }
    if status:
        payload["query"].update({"status": status})  # type: ignore
    if skip:
        payload.update({"skip": skip})  # type: ignore
    if limit:
        payload.update({"limit": limit})  # type: ignore

    view_result = http.results.view(payload)
    table.add_column("ID", max_width=50, justify="left", style="bright_blue")
    table.add_column("Pipeline", max_width=50, justify="left", style="bright_blue")
    table.add_column("Products", max_width=50, justify="left")
    table.add_column("Plots", max_width=50, justify="left")
    table.add_column("Function", max_width=50, justify="left")
    table.add_column("Command", max_width=50, justify="left")
    table.add_column("Status", max_width=50, justify="left")
    for result in view_result:
        result_status = Text(result["status"], style=status_colors[result["status"]])
        has_products = "Yes" if result["products"] else "No"
        has_products = Text(has_products, style=yes_no_colors[has_products.lower()])
        has_plots = "Yes" if result["plots"] else "No"
        has_plots = Text(has_plots, style=yes_no_colors[has_plots.lower()])
        _function = (
            result["function"] if result["function"] else Text("-------", style="red")
        )
        table.add_row(
            result["id"],
            result["pipeline"],
            has_products,
            has_plots,
            _function,
            " ".join(result["command"]),
            result_status,
        )
    console.print(table)


@results.command("inspect", help="Returns detailed information about specified Result.")
@click.argument("pipeline", type=str, required=True)
@click.argument("id", type=str, required=True)
def inspect(pipeline: str, id: str):
    """Returns details for one specific results.

    Parameters
    ----------
    pipeline : str
        Pipeline name.
    id : str
        Results ID.
    """
    http = HTTPContext()
    payload = {
        "query": {"pipeline": pipeline, "id": id},
    }
    inspect_result = http.results.view(payload)[0]
    table.add_column(f"{pipeline} - {id}", max_width=100, justify="left")
    table.add_row(JSON(dumps(inspect_result), indent=2))
    console.print(table)
