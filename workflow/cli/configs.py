"""Manage workflow pipelines."""

import json
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import click
import requests
import yaml
from rich import pretty
from rich.console import Console
from rich.progress import BarColumn, Progress, TextColumn
from rich.syntax import Syntax
from rich.table import Column, Table
from rich.text import Text
from yaml.loader import SafeLoader

from workflow.http.context import HTTPContext
from workflow.utils import format, validate
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
    http = HTTPContext(backends=["configs"])
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
    http = HTTPContext(backends=["configs"])
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
    http = HTTPContext(backends=["configs"])
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
    http = HTTPContext(backends=["configs", "pipelines"])
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


@configs.command("stop", help="Stop Pipelines related to a Config.")
@click.argument("config", type=str, required=True)
@click.argument("id", type=str, required=True)
def stop(config: str, id: str):
    """Stop managers for a Config."""
    http = HTTPContext(backends=["configs"])
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


@configs.command("rm", help="Removes a config.")
@click.argument("config", type=str, required=True)
@click.argument("id", type=str, required=True)
def rm(config: str, id: str):
    """Remove a config."""
    http = HTTPContext(backends=["configs"])
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


@configs.command("retry", help="Retry all Pipeline related to a Config.")
@click.argument("name", type=str, required=True)
@click.argument("id", type=str, required=True)
def retry(name: str, id: str):
    """Retry all Pipeline related to a Config.

    Parameters
    ----------
    name : str
        Config name.
    id : str
        Config ID.
    """
    http = HTTPContext(backends=["configs"])
    content = None
    try:
        retry_result = http.configs._retry(name, id)
    except Exception as e:
        text = Text(f"No configurations were retried.\nError: {e}", style="red")
        content = text
    else:
        table.add_column(
            retry_result["message"], max_width=50, justify="left", style="red"
        )
        content = table
    console.print(content)


@configs.command("reformat", help="Reformat V1 YAML files to V2.")
@click.argument(
    "filename",
    type=click.Path(exists=True, dir_okay=False, readable=True),
    required=True,
)
def reformat(filename: click.Path):
    """Reformat YAML file to V2.

    Parameters
    ----------
    filename : click.Path
        Filename.
    """
    filepath: str = str(filename)
    data: Dict[str, Any] = {}
    with open(filepath) as reader:
        data = yaml.load(reader, Loader=SafeLoader)  # type: ignore

    steps, matrix, version = format.needs_reformat(data)
    if any([steps, matrix, version]):
        console.print(Text("Version 1 YAML, reformatting...", style="red"))
        data = format.reformat(
            data=data,
            r_steps=steps,
            r_matrix=matrix,
            r_version=version,
            console=console,
        )
    else:
        console.print(Text("Reformat not needed.", style="red"))
        return

    with open(filepath, "w") as file:
        new_data: str = yaml.dump(data)
        file.write(new_data)
    console.print(f"Reformatted file {filename}", style="green")


@configs.command("migrate", help="Sends running Config to Pipelines V2.")
@click.argument("name", type=str, required=True)
@click.argument("base_url", type=str, required=True)
@click.option(
    "status",
    "-s",
    "--status",
    type=click.Choice(["success", "failure", "running", "queued", "cancelled"]),
    default="running",
)
@click.option("delete", "-d", "--delete", is_flag=True, default=False)
def migrate(name: str, base_url: str, status: str, delete: bool):
    """Migrates V1 Configs to V2.

    Parameters
    ----------
    name : str
        Configuration name.
    base_url : str
        Pipelines V1 backend URL.
    status : str
        Status filter.
    delete : bool
        WIP.
    """
    http = HTTPContext(backends=["configs"])
    params = {
        "skip": 0,
        "length": 100,
        "projection": json.dumps({}),
        "query": json.dumps({"status": {"$in": status.split(",")}}),
        "name": name,
    }
    url = f"{base_url}?{urlencode(params)}"
    response = requests.get(url)
    pipelines = response.json()
    text_column = TextColumn("{task.description}", table_column=Column(ratio=1))
    bar_column = BarColumn(bar_width=None, table_column=Column(ratio=2))
    progress = Progress(text_column, bar_column, expand=True)

    if not pipelines:
        console.print(f"No Config objects were found under the name {name}")
        return

    console.print(
        f"Migrating {len(pipelines)} Pipeline objects from {name} collection to V2.",
        style="bright_green",
    )
    with progress:
        for obj in pipelines:
            task = progress.add_task(f"[cyan]Migrating {obj['id']}", total=1)
            # ? Reformat
            reformatted_obj = format.reformat(
                data=obj,
                r_steps=False,
                r_matrix=False,
                r_version=True,
            )
            yaml_url = (
                f"{base_url}/inspect?"
                f"{urlencode({'name': name, 'id': reformatted_obj['id']})}"
            )
            yaml_response = requests.get(yaml_url)
            old_yaml = yaml_response.json()["yaml"]
            new_yaml = format.reformat(
                data=yaml.safe_load(old_yaml),
                r_steps=True,
                r_matrix=True,
                r_version=True,
            )
            progress.update(task, advance=0.3)
            reformatted_obj["yaml"] = yaml.dump(new_yaml)
            # ? Stop monitoring on V1
            stopped = False
            if obj["status"] == "running":
                stop_params = urlencode(
                    {"name": obj["name"], "query": json.dumps({"id": obj["id"]})}
                )
                stop_url = f"{base_url}/cancel?" f"{stop_params}"
                stop_response = requests.put(stop_url)
                if stop_response.ok:
                    stopped = True
                    progress.update(task, advance=0.3)
            # ? Migrate
            migration_response = http.configs.migrate(reformatted_obj)
            if migration_response.ok:
                progress.update(task, advance=0.4 if stopped else 0.7)
        console.print("Migration completed", style="bright_green")
