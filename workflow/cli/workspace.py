"""Workflow Workspace CLI."""

from pathlib import Path
from typing import Any, Dict

import click
from rich import pretty
from rich.console import Console
from rich.table import Table
from yaml import dump

from workflow import DEFAULT_WORKSPACE_PATH, MODULE_PATH
from workflow.utils import read as reader
from workflow.utils.logger import get_logger

logger = get_logger("workflow.cli.workspace")

pretty.install()
console = Console()

localspaces = Path(DEFAULT_WORKSPACE_PATH).parent
localstems = [space.stem for space in localspaces.glob("*.y*ml")]
modulespaces = Path(MODULE_PATH, "workflow", "workspaces")
modulestems = [space.stem for space in modulespaces.glob("*.y*ml")]


@click.group(name="workspace", help="Manage Workflow Workspaces.")
def workspace():
    """Manage Workflow Workspaces."""
    pass


@workspace.command("ls", help="List workspaces.")
def ls():
    """List all workspaces."""
    table = Table(
        title="\nWorkflow Workspaces",
        header_style="magenta",
        title_style="bold magenta",
    )
    table.add_column("Workspace", style="cyan", justify="right")
    table.add_column("Source", style="green", justify="left")
    table.add_row("", "From Workflow Python Module", style="red italic")
    for workspace in modulespaces.glob("*.y*ml"):
        table.add_row(workspace.stem, workspace.as_posix())
    table.add_row("", "From Local Configuration Folder", style="red italic")
    for workspace in localspaces.glob("*.y*ml"):
        if workspace.stem == "workspace":
            table.add_row(
                f"{workspace.stem} (active)", workspace.as_posix(), style="italic"
            )
        else:
            table.add_row(workspace.stem, workspace.as_posix())
    console.print(table)


@workspace.command("set", help="Set the active workspace.")
@click.argument(
    "workspace",
    type=str,
    required=True,
    nargs=1,
)
def set(workspace: str):
    """Set the active workspace.

    Args:
        workspace (str): The workspace to set. The workspace
            argument can be a url, a local path, or a name of
            a local workspace.
        debug (bool, optional): Debug Logs. Defaults to False.
    """
    config: Dict[str, Any] = {}
    console.print(f"Locating workspace {workspace}", style="italic blue")
    if Path(workspace).absolute().exists():
        console.print(f"Reading {workspace}", style="italic blue")
        config = reader.workspace(Path(workspace).absolute())
    elif workspace in localstems:
        for possibility in localspaces.glob(f"{workspace}.y*ml"):
            console.print(f"Reading {possibility}", style="italic blue")
            config = reader.workspace(possibility)
            break
    elif workspace in [space.stem for space in modulespaces.glob("*.y*ml")]:
        for possibility in modulespaces.glob(f"{workspace}.y*ml"):
            console.print(f"Reading {possibility}", style="italic blue")
            config = reader.workspace(possibility)
            break
    else:
        console.print(f"Workspace {workspace} not found.", style="bold red")
        return

    name: str = config["workspace"]
    localspaces.mkdir(parents=True, exist_ok=True)
    activepath = localspaces / "workspace.yml"
    # Write config to activepath, even if it already exists.
    with open(activepath, "w") as filename:
        dump(config, filename)
        console.print(f"Workspace {name} set to active.", style="bold green")


@workspace.command("read", help="Read workspace config.")
@click.argument("workspace", type=str, required=True, nargs=1, default="workspace")
def read(workspace: str):
    """Read the active workspace.

    Args:
        workspace (str): The workspace to read.
    """
    if workspace in localstems:
        for possibility in localspaces.glob(f"{workspace}.y*ml"):
            console.print(f"Reading {possibility}", style="italic blue")
            config = reader.workspace(possibility)
            console.print(config, style="green")
            return
    elif workspace in modulestems:
        for possibility in modulespaces.glob(f"{workspace}.y*ml"):
            console.print(f"Reading {possibility}", style="italic blue")
            config = reader.workspace(possibility)
            console.print(config, style="green")
            return
    else:
        console.print("No local workspace found.", style="italic bold red")
    # Check if workspace is a url.
    if "://" in workspace:
        console.print("Reading from URL.", style="italic blue")
        config = reader.workspace(workspace)
        console.print(config, style="green")
        return


@workspace.command("unset", help="Unset active workspace.")
def unset():
    """Unset the active workspace."""
    # Set the default console style.
    console.print("Removing the active workspace.", style="italic red")
    # If the workspace already exists, warn the user.
    (localspaces / "workspace.yml").unlink(missing_ok=True)
    console.print("Workspace Removed.", style="bold red")


@workspace.command("purge", help="Purge all local workspaces.")
def purge():
    """Purge all local workspaces."""
    # Remove all files from ~/.config/workflow/
    console.print("Purging all local workspaces", style="italic red")
    for workspace in localspaces.glob("*.y*ml"):
        console.print(f"Removing {workspace}", style="italic red")
        workspace.unlink()
    console.print("Done.", style="bold red")
