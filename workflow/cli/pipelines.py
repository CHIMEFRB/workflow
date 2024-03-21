"""Manage workflow pipelines."""

import json
from typing import Any, Dict, Optional, Tuple

import click
import requests
import yaml
from rich import pretty
from rich.console import Console
from rich.json import JSON
from rich.table import Table
from rich.text import Text
from yaml.loader import SafeLoader

from workflow.http.context import HTTPContext

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
status_colors = {
    "active": "bright_blue",
    "running": "blue",
    "created": "lightblue",
    "queued": "yellow",
    "success": "green",
    "failure": "red",
    "cancelled": "dark_goldenrod",
    "expired": "dark_goldenrod",
}


@click.group(name="pipelines", help="Manage Workflow Pipelines.")
def pipelines():
    """Manage workflow pipelines."""
    pass


@pipelines.command("version", help="Backend version.")
def version():
    """Get version of the pipelines service."""
    http = HTTPContext()
    console.print(http.pipelines.info())


@pipelines.command("ls", help="List pipelines.")
@click.option(
    "name",
    "--name",
    "-n",
    type=str,
    required=False,
    help="List only Pipelines with provided name.",
)
@click.option(
    "--schedule", "-sch", is_flag=True, help="For interacting with the Schedule API."
)
def ls(name: Optional[str] = None, schedule: bool = False):
    """List all pipelines."""
    http = HTTPContext()
    objects = (
        http.pipelines.list_pipeline_configs(name)
        if not schedule
        else http.pipelines.list_schedules(name)
    )
    if schedule:
        table.title = "Workflow Scheduled Pipelines"
        table.add_column("ID", max_width=50, justify="left", style="blue")
        table.add_column("Name", max_width=50, justify="left", style="bright_green")
        table.add_column("Status", max_width=50, justify="left")
        table.add_column("Lives", max_width=50, justify="left")
        table.add_column("Has Spawned", max_width=50, justify="left")
        table.add_column("Next Time", max_width=50, justify="left")
        for schedule_obj in objects:
            status = Text(
                schedule_obj["status"], style=status_colors[schedule_obj["status"]]
            )
            lives = schedule_obj["lives"]
            lives_text = Text(str(lives) if lives > -1 else "\u221e")
            table.add_row(
                schedule_obj["id"],
                schedule_obj["pipeline_config"]["name"],
                status,
                lives_text,
                str(schedule_obj["has_spawned"]),
                str(schedule_obj["next_time"]),
            )
    else:
        table.add_column("ID", max_width=50, justify="left", style="blue")
        table.add_column("Name", max_width=50, justify="left", style="bright_green")
        table.add_column("Status", max_width=50, justify="left")
        table.add_column("Stage", max_width=50, justify="left")
        for config in objects:
            status = Text(config["status"], style=status_colors[config["status"]])
            table.add_row(
                config["id"], config["name"], status, str(config["current_stage"])
            )
    console.print(table)


@pipelines.command("count", help="Count pipeline configurations per collection.")
@click.option(
    "--schedule", "-sch", is_flag=True, help="For interacting with the Schedule API."
)
def count(schedule: bool):
    """Count pipeline configurations."""
    http = HTTPContext()
    counts = (
        http.pipelines.count() if not schedule else http.pipelines.count_schedules()
    )
    if schedule:
        table.title = "Workflow Schedule Pipelines"
    table.add_column("Name", max_width=50, justify="left", style="blue")
    table.add_column("Count", max_width=50, justify="left")
    total = int()
    for k, v in counts.items():
        table.add_row(k, str(v))
        total += v
    table.add_section()
    table.add_row("Total", str(total))
    console.print(table)


@pipelines.command("deploy", help="Deploy a workflow pipeline.")
@click.option(
    "--schedule", "-sch", is_flag=True, help="For interacting with the Schedule API."
)
@click.argument(
    "filename",
    type=click.Path(exists=True, dir_okay=False, readable=True),
    required=True,
)
def deploy(filename: click.Path, schedule: bool):
    """Deploy a workflow pipeline."""
    http = HTTPContext()
    filepath: str = str(filename)
    data: Dict[str, Any] = {}
    with open(filepath) as reader:
        data = yaml.load(reader, Loader=SafeLoader)  # type: ignore
    if schedule and "schedule" not in data.keys():
        error_text = Text(
            "Your configuration file needs a schedule when using the --schedule option",
            style="red",
        )
        console.print(error_text)
        return
    try:
        deploy_result = http.pipelines.deploy(data, schedule)
        print(deploy_result)
    except requests.HTTPError as deploy_error:
        console.print(deploy_error.response.json()["message"])
        return
    table.add_column("IDs", max_width=50, justify="left", style="bright_green")
    if isinstance(deploy_result, list):
        for _id in deploy_result:
            table.add_row(_id)
    if isinstance(deploy_result, dict):
        for v in deploy_result.values():
            table.add_row(v)
    console.print(table)


@pipelines.command("ps", help="Get pipeline details.")
@click.argument("pipeline", type=str, required=True)
@click.argument("id", type=str, required=True)
@click.option(
    "--schedule", "-sch", is_flag=True, help="For interacting with the Schedule API."
)
def ps(pipeline: str, id: str, schedule: bool):
    """List a pipeline configuration in detail."""
    http = HTTPContext()
    query: Dict[str, Any] = {"id": id}
    console_content = None
    try:
        payload = http.pipelines.get_pipeline_config(pipeline, query, schedule)
    except IndexError:
        error_text = Text(
            f"No {'Schedule' if schedule else 'PipelineConfig'} were found", style="red"
        )
        console_content = error_text
    else:
        if not schedule:
            table.add_column(f"Pipeline: {pipeline}", max_width=120, justify="left")
        else:
            table.add_column(
                f"Scheduled Pipeline: {pipeline}", max_width=120, justify="left"
            )
        text = JSON(json.dumps(payload), indent=2)
        table.add_row(text)
        console_content = table
    finally:
        console.print(console_content)


@pipelines.command("stop", help="Kill a running pipeline.")
@click.argument("pipeline", type=str, required=True)
@click.argument("id", type=str, required=True)
def stop(pipeline: str, id: Tuple[str]):
    """Kill a running pipeline."""
    http = HTTPContext()
    stop_result = http.pipelines.stop(pipeline, id)
    if not any(stop_result):
        text = Text("No pipeline configurations were stopped.", style="red")
        console.print(text)
        return
    table.add_column("Stopped IDs", max_width=50, justify="left")
    for config in stop_result:
        table.add_row(config["id"])
    console.print(table)


@pipelines.command("rm", help="Remove a pipeline.")
@click.argument("pipeline", type=str, required=True)
@click.argument("id", type=str, required=True)
@click.option(
    "--schedule", "-sch", is_flag=True, help="For interacting with the Schedule API."
)
def rm(pipeline: str, id: Tuple[str], schedule: bool):
    """Remove a pipeline."""
    http = HTTPContext()
    content = None
    try:
        delete_result = http.pipelines.remove(pipeline, id, schedule)
        if delete_result.status_code == 204:
            text = Text("No pipeline configurations were deleted.", style="red")
            content = text
    except Exception as e:
        text = Text(
            f"No pipeline configurations were deleted.\nError: {e}", style="red"
        )
        content = text
    else:
        table.add_column("Deleted IDs", max_width=50, justify="left", style="red")
        table.add_row(id)
        content = table
    console.print(content)


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
