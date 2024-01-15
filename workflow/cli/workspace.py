"""Workflow Workspace CLI."""

from pathlib import Path
from typing import Any, Dict

import click
from rich import pretty
from rich.console import Console
from rich.table import Table
from yaml import dump

from workflow import CONFIG_PATH, MODULE_PATH
from workflow.utils import read as reader

pretty.install()
console = Console()

# Local Workflow configurations are kept in ~/.workflow/
localspaces: Path = CONFIG_PATH / "workspaces"


@click.group(name="workspace", help="Manage workflow workspaces.")
def workspace():
    """Manage Workspaces."""
    pass


@workspace.command("ls", help="List workspaces.")
def ls():
    """List all workspaces."""
    table = Table(
        title="\nWorkflow Workspaces",
        show_header=True,
        header_style="magenta",
        title_style="bold magenta",
    )
    table.add_column("Workspace", style="cyan", justify="right")
    table.add_column("Source", style="green", justify="left")
    table.add_row("", "from workflow package", style="red italic")
    for workspace in Path(MODULE_PATH, "workflow", "workspaces").glob("*.y*ml"):
        table.add_row(workspace.stem, workspace.as_posix())
    table.add_row("", "from config folder", style="red italic")
    for workspace in localspaces.glob("*.y*ml"):
        table.add_row(workspace.stem, workspace.as_posix())
    console.print(table)


@workspace.command("set", help="Set the active workspace.")
@click.option("--debug", is_flag=True, help="Print debug information.")
@click.argument("workspace", type=str, required=True, nargs=1)
def set(workspace: str, debug: bool = False):
    """Set the active workspace.

    Args:
        workspace (str): The workspace to set. The workspace
            argument can be a url, a local path, or a name of
            a local workspace.
        debug (bool, optional): Debug Logs. Defaults to False.
    """
    console.print(f"Retrieving {workspace}", style="italic blue")
    config: Dict[str, Any] = reader.workspace(workspace)
    name: str = config["workspace"]
    console.print(f"Discovered workspace {name}", style="italic blue")
    if debug:
        console.print(config, style="green")
    # Create the ~/.workflow/workspaces/
    localspaces.mkdir(parents=True, exist_ok=True)
    # Copy the workspace to ~/.workflow/workspaces/<name>.yml
    console.print(f"Writing {localspaces / f'{name}.yml'}", style="italic green")
    with open(localspaces / f"{name}.yml", "w") as filename:
        dump(config, filename)
    console.print(f"Writing {localspaces / 'active.yml'}", style="italic green")
    # Copy the workspace to ~/.workflow/workspaces/active.yml
    with open(localspaces / "active.yml", "w") as filename:
        dump(config, filename)
    console.print(f"Workspace {name} set.", style="bold green")


@workspace.command("read", help="Read workspace config.")
@click.option(
    "--source", "-s", type=str, required=True, help="Source can be url, path, or name"
)
def read(source: str):
    """Read the workspace config.

    Args:
        source (str): The source of the workspace config.
    """
    try:
        if source == "active":
            source = (localspaces / "active.yml").as_posix()
        config: Dict[str, Any] = reader.workspace(source)
        console.print(config, style="green")
    except Exception as error:
        console.print(error, style="red")


@workspace.command("unset", help="Unset active workspace.")
def unset():
    """Unset the active workspace."""
    # Set the default console style.
    console.print("Removing the active workspace.", style="italic red")
    # If the workspace already exists, warn the user.
    (localspaces / "active.yml").unlink(missing_ok=True)
    console.print("Workspace Removed.", style="bold red")


@workspace.command("purge", help="Purge all local workspaces.")
def purge():
    """Purge all local workspaces."""
    # Remove all files from ~/.workflow/workspaces/
    console.print("Purging all local workspaces", style="italic red")
    for workspace in localspaces.glob("*.y*ml"):
        console.print(f"Removing {workspace}", style="italic red")
        workspace.unlink()
    console.print("Done.", style="bold red")
