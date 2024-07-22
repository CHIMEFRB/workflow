"""Manage workflow pipelines."""

import json
from typing import Any, Dict, Optional

import click
import requests
from rich import pretty
from rich.console import Console
from rich.table import Table
from rich.text import Text

from workflow.http.context import HTTPContext
from workflow.utils.renderers import render_pipeline
from workflow.utils.variables import status_colors

pretty.install()
console = Console()

table = Table(
    title="\nWorkflow Pipelines",
    show_header=True,
    header_style="magenta",
    title_style="bold magenta",
    min_width=50,
)

BASE_URL = "https://frb.chimenet.ca/pipelines"
STATUS = ["created", "queued", "running", "success", "failure", "cancelled"]


@click.group(name="pipelines", help="Manage Workflow Pipelines.")
def pipelines():
    """Manage Workflow Pipelines."""
    pass


@pipelines.command("version", help="Backend version.")
def version():
    """Get version of the pipelines service."""
    http = HTTPContext()
    console.print(http.pipelines.info())


@pipelines.command("ls", help="List pipelines.")
@click.argument("name", type=str, required=False)
@click.option(
    "quiet",
    "--quiet",
    "-q",
    is_flag=True,
    required=False,
    help="Only show IDs.",
)
def ls(name: Optional[str] = None, quiet: Optional[bool] = False):
    """List all pipelines."""
    pipelines_columns = ["status", "current_stage", "steps"]
    http = HTTPContext()
    objects = http.pipelines.list_pipelines(name)
    table.add_column("ID", max_width=100, justify="left", style="blue")
    for key in pipelines_columns:
        table.add_column(
            key.capitalize().replace("_", " "),
            max_width=50,
            justify="left",
        )
    for obj in objects:
        if not quiet:
            status = Text(obj["status"], style=status_colors[obj["status"]])
            table.add_row(
                obj["id"], status, str(obj["current_stage"]), str(len(obj["steps"]))
            )
            continue
        table.add_row(obj["id"])
    console.print(table)


@pipelines.command("count", help="Count pipeline configurations per collection.")
def count():
    """Count pipeline configurations."""
    http = HTTPContext()
    counts = http.pipelines.count()
    table.add_column("Name", max_width=50, justify="left", style="blue")
    table.add_column("Count", max_width=50, justify="left")
    total = int()
    for k, v in counts.items():
        table.add_row(k, str(v))
        total += v
    table.add_section()
    table.add_row("Total", str(total))
    console.print(table)


@pipelines.command("ps", help="Get pipeline details.")
# @click.argument("pipeline", type=str, required=True)
@click.argument("id", type=str, required=True)
def ps(id: str):
    """List a pipeline configuration in detail."""
    http = HTTPContext()
    query: str = json.dumps({"id": id})
    projection: str = json.dumps({})
    console_content = None
    column_max_width = 300
    column_min_width = 40
    # ? Get Config name, needed for querying the pipeline
    try:
        config_name = http.configs.get_configs(
            query=json.dumps({"pipelines": id}), projection=json.dumps({"name": 1})
        )[0]["name"]
    except Exception:
        error_text = Text(
            f"Could not found any Config parent for Pipeline {id}.", style="red"
        )
        console.print(error_text)
        return
    # ? Get the pipeline
    try:
        payload = http.pipelines.get_pipelines(
            name=config_name, query=query, projection=projection
        )[
            0  # type: ignore
        ]
    except IndexError:
        error_text = Text("No Pipelines were found", style="red")
        console_content = error_text
    else:
        text = Text()
        table.add_column(
            f"Pipeline: {config_name}",
            min_width=column_min_width,
            max_width=column_max_width,
            justify="left",
        )
        text.append(render_pipeline(payload))
        table.add_row(text)
        console_content = table
    finally:
        console.print(console_content)


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
