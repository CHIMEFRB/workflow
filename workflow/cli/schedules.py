"""Manage workflow pipelines schedules."""

from datetime import datetime
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
from workflow.utils.variables import status_colors

pretty.install()
console = Console()

table = Table(
    title="\nWorkflow Pipelines - Schedules",
    show_header=True,
    header_style="magenta",
    title_style="bold green",
    min_width=50,
)
BASE_URL = "https://frb.chimenet.ca/schedule"
STATUS = ["active", "running", "expired"]


@click.group(name="schedules", help="Manage Workflow Schedules.")
def schedules():
    """Manage Workflow Schedules."""
    pass


@schedules.command("version", help="Backend version.")
def version():
    """Get version of the pipelines service."""
    http = HTTPContext()
    console.print(http.pipelines.info())


@schedules.command("ls", help="List schedules.")
@click.option(
    "name",
    "--name",
    "-n",
    type=str,
    required=False,
    help="List only Schedules with provided name.",
)
@click.option(
    "quiet",
    "--quiet",
    "-q",
    is_flag=True,
    required=False,
    help="Only show IDs.",
)
def ls(name: Optional[str] = None, quiet: Optional[bool] = False):
    """List schedules.

    Parameters
    ----------
    name : Optional[str], optional
        Name of specific schedule, by default None
    quiet : Optional[bool], optional
        Whether to show only IDs.
    """
    http = HTTPContext()
    objects = http.schedules.list_schedules(name)
    table.title = "Workflow Scheduled Pipelines"
    table.add_column("ID", max_width=50, justify="left", style="blue")
    if not quiet:
        table.add_column("Name", max_width=50, justify="left", style="bright_green")
        table.add_column("Status", max_width=50, justify="left")
        table.add_column("Lives", max_width=50, justify="left")
        table.add_column("Has Spawned", max_width=50, justify="left")
        table.add_column("Next Time", max_width=50, justify="left")
    for schedule_obj in objects:
        if not quiet:
            status = Text(
                schedule_obj["status"], style=status_colors[schedule_obj["status"]]
            )
            lives = schedule_obj["lives"]
            lives_text = Text(str(lives) if lives > -1 else "\u221e")
            table.add_row(
                schedule_obj["id"],
                schedule_obj["config"]["name"],
                status,
                lives_text,
                str(schedule_obj["has_spawned"]),
                str(schedule_obj["next_time"]),
            )
            continue
        table.add_row(schedule_obj["id"])
    console.print(table)


@schedules.command("count", help="Count schedules per collection.")
def count():
    """Count schedules."""
    http = HTTPContext()
    counts = http.schedules.count_schedules()
    table.title = "Workflow Schedules"
    table.add_column("Name", max_width=50, justify="left", style="blue")
    table.add_column("Count", max_width=50, justify="left")
    total = int()
    for k, v in counts.items():
        table.add_row(k, str(v))
        total += v
    table.add_section()
    table.add_row("Total", str(total))
    console.print(table)


@schedules.command("deploy", help="Deploy a scheduled pipeline.")
@click.argument(
    "filename",
    type=click.Path(exists=True, dir_okay=False, readable=True),
    required=True,
)
def deploy(filename: click.Path):
    """Deploy a scheduled pipeline."""
    http = HTTPContext()
    filepath: str = str(filename)
    data: Dict[str, Any] = {}
    with open(filepath) as reader:
        data = yaml.load(reader, Loader=SafeLoader)  # type: ignore
    try:
        deploy_result = http.schedules.deploy(data)
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


@schedules.command("ps", help="Get schedule details.")
@click.argument("id", type=str, required=True)
@click.option(
    "--details",
    is_flag=True,
    show_default=True,
    help="Returns the Schedule Payload.",
)
def ps(id: str, details: Optional[bool] = False):
    """Gets schedules details."""
    http = HTTPContext()
    query: Dict[str, Any] = {"id": id}
    console_content = None
    key_nicknames = {
        "id": "ID",
        "crontab": "Crontab",
        "lives": "To Spawn",
        "has_spawned": "Has Spawned",
        "status": "Status",
        "next_time": "Next Execution",
        "history": "History",
    }
    try:
        payload = http.schedules.get_schedule(query)
    except IndexError:
        error_text = Text("No Schedule was found", style="red")
        console_content = error_text
    else:
        table.add_column(
            f"Scheduled Pipeline: {payload['config']['name']}",
            max_width=120,
            min_width=50,
            justify="left",
        )
        text = Text("")
        for k, v in payload.items():
            if k == "config":
                continue
            if k == "history":
                key_value_text = Text(
                    f"{key_nicknames.get(k, k)}: \n", style="bright_green"
                )
                for history in v:
                    history_dt = datetime.fromisoformat(history[0])
                    legible_dt = history_dt.strftime("%B %d, %Y at %I:%M:%S %p")
                    id = history[1]
                    key_value_text.append(f"-- {legible_dt}:", style="bright_blue")
                    key_value_text.append(f"\n\t{id}\n\n", style="white")
                text.append_text(key_value_text)
                continue
            key_value_text = Text(f"{key_nicknames.get(k, k)}: ", style="bright_green")
            key_value_text.append(
                f"{v}\n", style="white" if k != "status" else status_colors[v]
            )
            text.append_text(key_value_text)
        if details:
            table.add_column("Details", style="magenta")
            this_payload = JSON.from_data(payload["config"], indent=2)
            table.add_row(text, this_payload)
        else:
            table.add_row(text)
        console_content = table
    finally:
        console.print(console_content)


@schedules.command("rm", help="Remove a schedule.")
@click.argument("id", type=str, required=True)
def rm(id: Tuple[str]):
    """Remove a schedule."""
    http = HTTPContext()
    content = None
    try:
        delete_result = http.schedules.remove(id)
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
