"""Manage workflow pipelines."""
import json
from typing import Any, Dict, Optional

import click
import requests
from rich import pretty
from rich.console import Console
from rich.table import Table

pretty.install()
console = Console()

BASE_URL = "https://frb.chimenet.ca/pipelines"
DOTS: Dict[str, str] = {
    "accepted": "[blue]●[/blue]",
    "queued": "[yellow]●[/yellow]",
    "running": "[orange]●[/orange]",
    "success": "[green]●[/green]",
    "failure": "[red]●[/red]",
    "unknown": "[grey]●[/grey]",
}


@click.group(name="pipelines", help="Manage workflow pipelines.")
def pipelines():
    """Manage workflow pipelines."""
    pass


@pipelines.command("ls", help="List all active pipelines.")
def ls():
    """List all active pipelines."""
    pipelines = status()
    table = Table(
        title="\nWorkflow Pipelines",
        show_header=True,
        header_style="magenta",
        title_style="bold magenta",
    )
    table.add_column("Pipeline", max_width=50, justify="left")
    table.add_column("Count", max_width=50, justify="left")
    for key, value in pipelines.items():
        table.add_row(str(key), str(value))
    console.print(table)


@pipelines.command("ps", help="List all pipeline in detail.")
@click.argument("pipeline", type=str, required=True)
@click.argument("id", type=str, required=False)
def ps(pipeline: str, id: str):
    """List all pipeline in detail."""
    if not id:
        response = status(pipeline=pipeline, projection={"status": True, "id": True})
        info = response.get(pipeline)
        table = Table(
            title=f"\nWorkflow Pipeline: {pipeline}",
            show_header=True,
            header_style="magenta",
            title_style="bold magenta",
        )
        table.add_column("ID", max_width=50, justify="left")
        table.add_column("Status", max_width=50, justify="left")
        for item in info:
            pid = str(item.get("id"))
            pstatus = str(item.get("status"))
            table.add_row(pid, pstatus)
        console.print(table)
    if id:
        response = status(
            pipeline=pipeline, query={"id": id}, projection={"pipeline.work": False}
        )
        info = response.get(pipeline)[0]
        console.print(info)


@pipelines.command("version", help="Get version of the pipelines backend.")
def version():
    """Get version of the pipelines service."""
    response = requests.get(f"{BASE_URL}/version")
    console.print(response.json())


def status(
    pipeline: Optional[str] = None,
    query: Optional[Dict[str, Any]] = None,
    projection: Optional[Dict[str, bool]] = None,
    version: str = "v1",
):
    """Get status of all pipelines."""
    projected: str = ""
    filter: str = ""
    if projection:
        projected = str(json.dumps(projection))
    if query:
        filter = str(json.dumps(query))
    response = requests.get(
        f"{BASE_URL}/{version}/pipelines",
        params={"name": pipeline, "projection": projected, "query": filter},
    )
    return response.json()
