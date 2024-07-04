"""Fetch and process Work using any method compatible with Tasks API."""

import platform
import signal
from pathlib import Path
from sys import stderr, stdout
from threading import Event
from typing import Any, Dict, List, Optional, Tuple, Union

import click
from click_params import JSON, URL, FirstOf
from rich.console import Console

from workflow import DEFAULT_WORKSPACE_PATH
from workflow.http.context import HTTPContext
from workflow.lifecycle import attempt, configure
from workflow.utils import read
from workflow.utils.logger import get_logger

logger = get_logger("workflow.cli")

localspaces = Path(DEFAULT_WORKSPACE_PATH).parent


@click.command("run", short_help="Fetch & Perform Work.")
@click.argument("bucket", type=str, nargs=-1, required=True)
@click.option(
    "-s",
    "--site",
    type=click.STRING,
    required=True,
    show_default=True,
    help="filter work by site.",
)
@click.option(
    "-t",
    "--tag",
    type=click.STRING,
    multiple=True,
    required=False,
    default=None,
    show_default=True,
    help="filter work by tag.(multiple allowed)",
)
@click.option(
    "-p",
    "--parent",
    type=click.STRING,
    multiple=True,
    required=False,
    default=None,
    show_default=True,
    help="filter work by parent.(multiple allowed)",
)
@click.option(
    "-e",
    "--event",
    type=click.INT,
    multiple=True,
    required=False,
    default=None,
    show_default=True,
    help="filter work by event.(multiple allowed)",
)
@click.option(
    "-f",
    "--function",
    type=click.STRING,
    required=False,
    default=None,
    show_default=True,
    help="ignores work, runs this function instead",
)
@click.option(
    "-c",
    "--command",
    type=click.STRING,
    required=False,
    default=None,
    show_default=True,
    help="ignores work, runs this command instead",
)
@click.option(
    "--lives",
    "-l",
    type=click.IntRange(min=-1),
    default=-1,
    show_default=True,
    help="count of work to perform.",
)
@click.option(
    "--sleep",
    type=click.IntRange(min=1, max=300),
    default=30,
    show_default=True,
    help="seconds to sleep between work.",
)
@click.option(
    "-w",
    "--workspace",
    type=FirstOf(
        click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True),
        URL,
        JSON,
    ),
    default=(DEFAULT_WORKSPACE_PATH.as_posix()),
    show_default=True,
    help="workspace config.",
)
@click.option(
    "--argsource",
    type=click.Choice(["parameters", "work"]),
    default="parameters",
    show_default=True,
    help="run function with parameters or work object.",
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    default="INFO",
    show_default=True,
    help="logging level.",
)
def run(
    bucket: Tuple[str],
    site: str,
    tag: Tuple[str],
    parent: Tuple[str],
    event: Tuple[int],
    function: str,
    command: str,
    lives: int,
    sleep: int,
    workspace: Union[str, Dict[Any, Any]],
    argsource: str,
    log_level: str,
):
    """Fetch and perform work."""
    tty: bool = stdout.isatty() or stderr.isatty()
    # Set logging level
    logger.root.setLevel(log_level)
    logger.root.handlers[0].setLevel(log_level)
    logger.info(f"Workspace: {workspace}")
    logger.info(f"Log Level: {log_level}")

    # Configure the runtime workspace
    configure.workspace(workspace=workspace)
    # At this point, the default workspace should exist
    config: Dict[str, Any] = {}
    config = read.workspace(DEFAULT_WORKSPACE_PATH)
    # Collect baseurls from the workspace
    baseurls: Dict[str, Any] = config.get("http", {}).get("baseurls", {})
    # Reformat the tags, parent and buckets
    tags: List[str] = list(tag)
    parents: List[str] = list(parent)
    buckets: List[str] = list(bucket)
    events: List[int] = list(event)
    # Setup and connect to the workflow backend
    logger.info(
        "[bold red]Workflow Run CLI[/bold red]", extra=dict(markup=True, color="green")
    )
    logger.info(f"Buckets  : {buckets}")
    logger.info(f"Function : {function}")
    logger.info(f"Argsource: {argsource}")
    logger.info(f"Command  : {command}")
    logger.info(f"Mode     : {'Static' if (function or command) else 'Dynamic'}")
    logger.info(f"Lives    : {'infinite' if lives == -1 else lives}")
    logger.info(f"Sleep    : {sleep}s")
    logger.info(f"Log Level: {log_level}")
    logger.info(
        "[bold red]Work Filters [/bold red]",
        extra=dict(markup=True, color="green"),
    )
    logger.info(f"Site   : {site}")
    logger.info(f"Tags   : {tags}") if tags else None
    logger.info(f"Parents: {parents}") if parents else None
    logger.info(
        "[bold red]Workspace Config[/bold red]",
        extra=dict(markup=True, color="green"),
    )
    logger.info(f"Baseurls: {baseurls}")

    logger.info(
        "[bold red]Execution Environment [/bold red]",
        extra=dict(markup=True, color="green"),
    )
    logger.info(f"Operating System: {platform.system()}")
    logger.info(f"Python Version  : {platform.python_version()}")
    logger.info(f"Python Compiler : {platform.python_compiler()}")
    logger.info(f"TTY Detected    : {tty}")
    # If both function and command are provided, raise an error
    if function and command:
        logger.error("Cannot provide both function and command. Exiting...")
        exit(1)
    logger.info(
        "[bold red]Backend Checks [/bold red]",
        extra=dict(markup=True, color="green"),
    )
    loki_status: bool = configure.loki(logger=logger, config=config)
    logger.info(f"Loki Logs: {'✅' if loki_status else '❌'}")
    http: HTTPContext = HTTPContext(backends=["buckets"])
    try:
        version: Dict[str, Any] = http.buckets.info()
        logger.debug(f"Buckets Version: {version.get('version')}")
        logger.info("Buckets  : ✅")
    except Exception:
        logger.error("unable to connect to buckets.")
        exit(1)
    logger.info("System Checks Complete")

    try:
        logger.info(
            "[bold]Starting Workflow Lifecycle[/bold]",
            extra=dict(markup=True, color="green"),
        )
        console = Console(force_terminal=True, tab_size=4)
        with console.status(
            status="",
            spinner="aesthetic" if tty else "dots",
            spinner_style="bold green",
            refresh_per_second=10 if tty else 1,
        ):
            lifecycle(
                buckets=buckets,
                function=function,
                command=command,
                argsource=argsource,
                lives=lives,
                sleep=sleep,
                site=site,
                tags=tags,
                parents=parents,
                events=events,
                config=config,
                http=http,
            )
    except Exception as error:
        logger.exception(error)
    finally:
        logger.info(
            "[bold]Workflow Lifecycle Complete[/bold]",
            extra=dict(markup=True, color="green"),
        )


def lifecycle(
    buckets: List[str],
    function: Optional[str],
    command: Optional[str],
    argsource: str,
    lives: int,
    sleep: int,
    site: str,
    tags: List[str],
    parents: List[str],
    events: List[int],
    config: Dict[str, Any],
    http: HTTPContext,
):
    """Run the workflow lifecycle."""
    # Start the exit event
    exit = Event()

    # Get any stop, kill, or terminate signals and set the exit event
    def quit(signo: int, _: Any):
        """Handle terminal signals."""
        logger.critical(f"Received terminal signal {signo}. Exiting...")
        exit.set()

    # Register the quit function to handle the signals
    for sig in ("TERM", "HUP", "INT"):
        signal.signal(getattr(signal, "SIG" + sig), quit)

    # Run the lifecycle until the exit event is set or the lifetime is reached
    while lives != 0 and not exit.is_set():
        attempt.work(
            buckets=buckets,
            function=function,
            command=command,
            argsource=argsource,
            site=site,
            tags=tags,
            parents=parents,
            events=events,
            config=config,
            http=http,
        )
        lives -= 1
        logger.debug(f"sleeping: {sleep}s")
        exit.wait(sleep)
        logger.debug(f"awake: {sleep}s")


if __name__ == "__main__":
    run()
