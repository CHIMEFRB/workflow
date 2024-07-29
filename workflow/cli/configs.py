"""Manage workflow pipelines."""

import json
from typing import Any, Dict, List, Optional

import click
import requests
import yaml
from rich import pretty
from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from yaml.loader import SafeLoader

from workflow.http.context import HTTPContext
from workflow.utils import validate
from workflow.utils.renderers import render_config

pretty.install()
console = Console()

table = Table(
    title="\nWorkflow Configs",
    show_header=True,
    header_style="magenta",
    title_style="bold magenta",
    min_width=50,
)

BASE_URL = "https://frb.chimenet.ca/pipelines"
STATUS = ["created", "queued", "running", "success", "failure", "cancelled"]


@click.group(name="configs", help="Manage Workflow Configs. Version 2.")
def configs():
    """Manage Workflow Configs."""
    pass


@configs.command("version", help="Backend version.")
def version():
    """Get version of the pipelines service."""
    http = HTTPContext()
    console.print(http.configs.info())


@configs.command("count", help="Count objects per collection.")
def count():
    """Count objects in a database."""
    http = HTTPContext()
    counts = http.configs.count()
    table.add_column("Name", max_width=50, justify="left", style="blue")
    table.add_column("Count", max_width=50, justify="left")
    total = int()
    for k, v in counts.items():
        table.add_row(k, str(v))
        total += v
    table.add_section()
    table.add_row("Total", str(total))
    console.print(table)


@configs.command("deploy", help="Deploy a workflow config.")
@click.argument(
    "filename",
    type=click.Path(exists=True, dir_okay=False, readable=True),
    required=True,
)
def deploy(filename: click.Path):
    """Deploy a workflow config.

    Parameters
    ----------
    filename : click.Path
        File path.
    """
    http = HTTPContext()
    filepath: str = str(filename)
    data: Dict[str, Any] = {}
    with open(filepath) as reader:
        data = yaml.load(reader, Loader=SafeLoader)  # type: ignore

    # ? Check unused deployments and orphaned steps
    unused_deployments: List[str] = list()
    orphaned_steps: List[str] = list()
    if data.get("deployments", None):
        unused_deployments, orphaned_steps = validate.deployments(config=data)
        if any(unused_deployments):
            answer = console.input(
                f"The following deployments are not being used: {unused_deployments},"
                " do you wish to continue? (Y/n):"
            )
            if answer.lower() != "y":
                console.print("Cancelling", style="red")
                return
        if any(orphaned_steps):
            answer = console.input(
                f"The following steps {orphaned_steps} does not have a runs_on "
                "even though you have defined deployments, "
                "do you wish to continue? (Y/n):",
            )
            if answer.lower() != "y":
                console.print("Cancelling", style="red")
                return

    try:
        deploy_result = http.configs.deploy(data)
    except requests.HTTPError as deploy_error:
        console.print(deploy_error.response.json()["error_description"][0]["msg"])
        return
    header_text = Text("Config deployed: ")
    header_text.append(data["name"], style="blink underline bright_blue")
    table.add_column(
        header=header_text,
        min_width=35,
        max_width=50,
        justify="left",
        style="bright_green",
    )
    if isinstance(deploy_result, dict):
        for k, v in deploy_result.items():
            if k == "config":
                row_text = Text(f"{k}: ", style="magenta")
                row_text.append(f"{v}", style="white")
                table.add_row(row_text)
            if k == "pipelines":
                row_text = Text(f"{k}:\n", style="bright_blue")
                for id in deploy_result[k]:
                    row_text.append(f"\t{id}\n", style="white")
                table.add_row(row_text)
    console.print(table)


@configs.command("ls", help="List Configs.")
@click.argument("name", type=str, required=False)
@click.option(
    "quiet",
    "--quiet",
    "-q",
    is_flag=True,
    default=False,
    help="Only show IDs.",
)
def ls(name: Optional[str] = None, quiet: bool = False):
    """List all objects."""
    configs_colums = ["name", "version", "pipelines", "user"]
    projection = {"yaml": 0, "deployments": 0}
    if quiet:
        projection = {"id": 1}
    http = HTTPContext()
    objects = http.configs.get_configs(name=name, projection=json.dumps(projection))

    # ? Add columns for each key
    table.add_column("ID", max_width=40, justify="left", style="blue")
    if not quiet:
        for key in configs_colums:
            table.add_column(
                key.capitalize().replace("_", " "),
                max_width=50,
                justify="left",
                style="bright_green" if key == "name" else "white",
            )

    for obj in objects:
        if not quiet:
            table.add_row(
                obj["id"],
                obj["name"],
                obj["version"],
                str(len(obj["pipelines"])),
                obj["user"],
            )
            continue
        table.add_row(obj["id"])
    console.print(table)


@configs.command("ps", help="Get Configs details.")
@click.argument("name", type=str, required=True)
@click.argument("id", type=str, required=True)
@click.option(
    "--details",
    is_flag=True,
    default=False,
    show_default=True,
    help="Show more details for the object.",
)
def ps(name: str, id: str, details: bool):
    """Show details for an object."""
    http = HTTPContext()
    query: str = json.dumps({"id": id})
    projection: str = json.dumps({})
    console_content = None
    column_max_width = 300
    column_min_width = 50
    try:
        payload = http.configs.get_configs(
            name=name, query=query, projection=projection
        )[0]
    except IndexError:
        error_text = Text("No Configs were found", style="red")
        console_content = error_text
    else:
        text = Text("")
        table.add_column(
            f"Config: {name}",
            min_width=column_min_width,
            max_width=column_max_width,
            justify="left",
        )
        text.append(render_config(http, payload))
        if details:
            table.add_column(
                "Details",
                max_width=column_max_width,
                min_width=column_min_width,
                justify="left",
            )
            _details = payload["yaml"]
            table.add_row(text, Syntax(_details, "yaml"))
        else:
            table.add_row(text)
        table.add_section()
        table.add_row(
            Text("Explore pipelines in detail: \n", style="magenta i").append(
                "workflow pipelines ps <pipeline_id>",
                style="dark_blue on cyan",
            )
        )
        console_content = table
    finally:
        console.print(console_content)


@configs.command("stop", help="Stop managers for a Config.")
@click.argument("config", type=str, required=True)
@click.argument("id", type=str, required=True)
def stop(config: str, id: str):
    """Stop managers for a Config."""
    http = HTTPContext()
    stop_result = http.configs.stop(config, id)
    if not any(stop_result):
        text = Text("No configurations were stopped.", style="red")
        console.print(text)
        return
    table.add_column("Stopped IDs", max_width=50, justify="left")
    text = Text()
    for k in stop_result.keys():
        if k == "stopped_config":
            text.append("Config: ", style="bright_blue")
            text.append(f"{stop_result[k]}\n")
        if k == "stopped_pipelines":
            text.append("Pipelines: \n", style="bright_blue")
            for id in stop_result["stopped_pipelines"]:
                text.append(f"\t{id}\n")
    table.add_row(text)
    console.print(table)


@configs.command("rm", help="Remove a config.")
@click.argument("config", type=str, required=True)
@click.argument("id", type=str, required=True)
def rm(config: str, id: str):
    """Remove a config."""
    http = HTTPContext()
    content = None
    try:
        delete_result = http.configs.remove(config, id)
        if delete_result.status_code == 204:
            text = Text("No pipeline configurations were deleted.", style="red")
            content = text
    except Exception as e:
        text = Text(f"No configurations were deleted.\nError: {e}", style="red")
        content = text
    else:
        table.add_column("Deleted IDs", max_width=50, justify="left", style="red")
        table.add_row(id)
        content = table
    console.print(content)
