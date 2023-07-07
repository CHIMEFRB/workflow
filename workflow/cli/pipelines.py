"""Manage workflow pipelines."""
import json
from typing import Any, Dict, Optional, Tuple

import click
import requests
import yaml
from rich import pretty
from rich.console import Console
from rich.table import Table
from yaml.loader import SafeLoader

pretty.install()
console = Console()

BASE_URL = "https://frb.chimenet.ca/pipelines"
STATUS = ["created", "queued", "running", "success", "failure", "cancelled"]


@click.group(name="pipelines", help="Manage Workflow Pipelines.")
def pipelines():
    """Manage workflow pipelines."""
    pass


@pipelines.command("version", help="Backend version.")
def version():
    """Get version of the pipelines service."""
    response = requests.get(f"{BASE_URL}/version")
    console.print(response.json())


@pipelines.command("ls", help="List pipelines.")
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


@pipelines.command("deploy", help="Deploy a workflow pipeline.")
@click.argument(
    "filename",
    type=click.Path(exists=True, dir_okay=False, readable=True),
    required=True,
)
def deploy(filename: click.Path):
    """Deploy a workflow pipeline."""
    filepath: str = str(filename)
    data: Dict[str, Any] = {}
    with open(filepath) as reader:
        data = yaml.load(reader, Loader=SafeLoader)  # type: ignore
    response = requests.post(f"{BASE_URL}/v1/pipelines", json=data)
    response.raise_for_status()
    pipeline: str = response.json().get("id")
    console.print(f"{pipeline}")


@pipelines.command("ps", help="Get pipeline details.")
@click.argument("pipeline", type=str, required=True)
@click.argument("id", type=str, required=False)
@click.option(
    "--filter",
    "-f",
    type=click.Choice(STATUS),
    required=False,
    help="Filter by status.",
)
@click.option("--quiet", "-q", is_flag=True, default=False, help="Only display  IDs.")
def ps(pipeline: str, id: str, filter: str, quiet: bool):
    """List all pipeline in detail."""
    query: Dict[str, Any] = {}
    if not id:
        if filter:
            query = {"status": filter}
        response = status(
            pipeline=pipeline, query=query, projection={"status": True, "id": True}
        )
        if not quiet:
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
        else:
            for item in response.get(pipeline):
                console.print(item.get("id"))
    if id:
        query = {"id": id}
        response = status(
            pipeline=pipeline, query=query, projection={"pipeline.work": False}
        )
        info = response.get(pipeline)[0]
        console.print(info)


@pipelines.command("stop", help="Kill a running pipeline.")
@click.argument("pipeline", type=str, required=True)
@click.argument("id", type=str, nargs=-1, required=True)
def stop(pipeline: str, id: Tuple[str]):
    """Kill a running pipeline."""
    filter: str = json.dumps({"id": {"$in": id}})
    try:
        response = requests.put(
            f"{BASE_URL}/v1/pipelines/cancel",
            params={"name": pipeline, "query": filter},
        )
        response.raise_for_status()
        console.print(f"{id}")
    except requests.exceptions.HTTPError as err:
        console.print(err)


@pipelines.command("rm", help="Remove a pipeline.")
@click.argument("pipeline", type=str, required=True)
@click.argument("id", type=str, nargs=-1, required=True)
def rm(pipeline: str, id: Tuple[str]):
    """Remove a pipeline."""
    filter: str = json.dumps({"id": {"$in": id}})
    try:
        response = requests.delete(
            f"{BASE_URL}/v1/pipelines",
            params={"name": pipeline, "query": filter},
        )
        response.raise_for_status()
        console.print(f"{id}")
    except requests.exceptions.HTTPError as err:
        console.print(err)


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
