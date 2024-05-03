"""Manage workflow pipelines."""

import json
from typing import Any, Dict, Optional

import click
import requests
import yaml
from rich import pretty
from rich.console import Console
from rich.json import JSON
from rich.table import Table
from rich.text import Text
from yaml import safe_load
from yaml.loader import SafeLoader

from workflow.http.context import HTTPContext
from workflow.utils.renderers import render_config, render_pipeline
from workflow.utils.variables import status_colors

pretty.install()
console = Console()

table = Table(
    title="\nWorkflow Pipelines",
    show_header=True,
    header_style="magenta",
    title_style="bold magenta",
    min_width=10,
)

BASE_URL = "https://frb.chimenet.ca/pipelines"
STATUS = ["created", "queued", "running", "success", "failure", "cancelled"]


@click.group(name="configs", help="Manage Workflow Configs. Version 2.")
def configs():
    """Manage workflow configs."""
    pass


@configs.command("version", help="Backend version.")
def version():
    """Get version of the pipelines service."""
    http = HTTPContext()
    console.print(http.configs.info())


@configs.command("count", help="Count objects per collection.")
@click.option(
    "--pipelines",
    "-p",
    is_flag=True,
    default=False,
    show_default=True,
    help="Use this command for pipelines database.",
)
def count(pipelines: bool):
    """Count objects in a database.

    Parameters
    ----------
    pipelines : bool
        Use this command on pipelines database.
    """
    http = HTTPContext()
    database = "pipelines" if pipelines else "configs"
    table.title += f" - {database.capitalize()}"
    counts = http.configs.count(database)
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
    try:
        deploy_result = http.configs.deploy(data)
    except requests.HTTPError as deploy_error:
        console.print(deploy_error.response.json()["error_description"][0]["msg"])
        return
    table.add_column("IDs", max_width=50, justify="left", style="bright_green")
    if isinstance(deploy_result, list):
        for _id in deploy_result:
            table.add_row(_id)
    if isinstance(deploy_result, dict):
        for v in deploy_result.values():
            table.add_row(v)
    console.print(table)


@configs.command("ls", help="List Configs.")
@click.option(
    "name",
    "--name",
    "-n",
    type=str,
    required=False,
    help="List only Configs with provided name.",
)
@click.option(
    "--pipelines",
    "-p",
    is_flag=True,
    default=False,
    show_default=True,
    help="Use this command for pipelines database.",
)
@click.option(
    "quiet",
    "--quiet",
    "-q",
    is_flag=True,
    default=False,
    help="Only show IDs.",
)
def ls(name: Optional[str] = None, pipelines: bool = False, quiet: bool = False):
    """List all objects."""
    database = "pipelines" if pipelines else "configs"
    table.title += f" - {database.capitalize()}"
    configs_colums = ["name", "version", "children", "user"]
    pipelines_columns = ["status", "current_stage", "steps"]
    projection = {"yaml": 0, "deployments": 0} if database == "configs" else {}
    if quiet:
        projection = {"id": 1}
    http = HTTPContext()
    objects = http.configs.get_configs(
        database=database, config_name=name, projection=json.dumps(projection)
    )

    # ? Add columns for each key
    table.add_column("ID", max_width=40, justify="left", style="blue")
    if not quiet:
        if database == "configs":
            for key in configs_colums:
                table.add_column(
                    key.capitalize().replace("_", " "),
                    max_width=50,
                    justify="left",
                    style="bright_green" if key == "name" else "white",
                )
        if database == "pipelines":
            for key in pipelines_columns:
                table.add_column(
                    key.capitalize().replace("_", " "),
                    max_width=50,
                    justify="left",
                )

    for obj in objects:
        if not quiet:
            if database == "configs":
                table.add_row(
                    obj["id"],
                    obj["name"],
                    obj["version"],
                    str(len(obj["children"])),
                    obj["user"],
                )
            if database == "pipelines":
                status = Text(obj["status"], style=status_colors[obj["status"]])
                table.add_row(
                    obj["id"], status, str(obj["current_stage"]), str(len(obj["steps"]))
                )
            continue
        table.add_row(obj["id"])
    console.print(table)


@configs.command("ps", help="Get Configs details.")
@click.argument("name", type=str, required=True)
@click.argument("id", type=str, required=True)
@click.option(
    "--pipelines",
    "-p",
    is_flag=True,
    default=False,
    show_default=True,
    help="Use this command for pipelines database.",
)
@click.option(
    "--details",
    "-d",
    is_flag=True,
    default=False,
    show_default=True,
    help="Show more details for the object.",
)
def ps(name: str, id: str, pipelines: str, details: bool):
    """Show details for an object."""
    http = HTTPContext()
    database = "pipelines" if pipelines else "configs"
    query: str = json.dumps({"id": id})
    projection: str = json.dumps({})
    console_content = None
    column_max_width = 300
    column_min_width = 40
    try:
        payload = http.configs.get_configs(
            database=database, config_name=name, query=query, projection=projection
        )[0]
    except IndexError:
        error_text = Text(f"No {database.capitalize()} were found", style="red")
        console_content = error_text
    else:
        text = Text("")
        if database == "pipelines":
            table.add_column(
                f"Pipeline: {name}",
                min_width=column_min_width,
                max_width=column_max_width,
                justify="left",
            )
            text.append(render_pipeline(payload))
        if database == "configs":
            table.add_column(
                f"Config: {name}",
                min_width=column_min_width,
                max_width=column_max_width,
                justify="left",
            )
            text.append(render_config(http, payload))
        if details:
            table.add_column("Details", max_width=column_max_width, justify="left")
            _details = safe_load(payload["yaml"])
            _details = {
                k: v
                for k, v in _details.items()
                if k not in ["name", "version", "deployments"]
            }
            table.add_row(text, JSON(json.dumps(_details), indent=2))
        else:
            table.add_row(text)
        console_content = table
    finally:
        console.print(console_content)
