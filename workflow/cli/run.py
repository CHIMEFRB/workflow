"""Fetch and process Work using any method compatible with Tasks API."""

import platform
import signal
import time
from pathlib import Path
from sys import stderr, stdout
from threading import Event
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import click
from click_params import JSON, URL, FirstOf
from rich.console import Console

from workflow import DEFAULT_WORKSPACE_PATH
from workflow.definitions.work import Work
from workflow.http.context import HTTPContext
from workflow.lifecycle import archive, container, execute
from workflow.utils import read, validate, write
from workflow.utils.logger import add_loki_handler, get_logger, set_tag, unset_tag

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
    help="filter work by tag.",
)
@click.option(
    "-p",
    "--parent",
    type=click.STRING,
    multiple=True,
    required=False,
    default=None,
    show_default=True,
    help="filter work by parent.",
)
@click.option(
    "-f",
    "--function",
    type=click.STRING,
    required=False,
    default=None,
    show_default=True,
    help="overload function to execute.",
)
@click.option(
    "-c",
    "--command",
    type=click.STRING,
    required=False,
    default=None,
    show_default=True,
    help="overload command to execute.",
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
    help="sleep between work attempts.",
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
    function: str,
    command: str,
    lives: int,
    sleep: int,
    workspace: Union[str, Dict[Any, Any]],
    log_level: str,
):
    """Fetch and perform work."""
    # Set logging level
    logger.root.setLevel(log_level)
    logger.root.handlers[0].setLevel(log_level)

    logger.info(f"Workspace: {workspace}")
    logger.info(f"Log Level: {log_level}")

    # workspace passed as a string for Path or URL
    if isinstance(workspace, str):
        if Path(workspace).absolute().exists():
            if workspace == DEFAULT_WORKSPACE_PATH.as_posix():
                logger.info("Running with active workspace.")
            else:
                logger.info(f"Saving {workspace} as active workspace.")
                # Save the workspace path to the default location
                write.workspace(Path(workspace))
        # Check if the workspace is a URL
        elif validate.url(workspace):
            logger.info(f"Running with workspace from URL {workspace}")
            # Fetch the workspace from the URL
            payload = read.url(workspace)
            # Save the workspace to the default location
            write.workspace(payload)

    if isinstance(workspace, dict):
        logger.info(f"Running with dict workspace: {workspace}")
        # Save the workspace to the default location
        write.workspace(workspace)

    # At this point, the default workspace should exist

    config: Dict[str, Any] = {}
    try:
        config = read.workspace(DEFAULT_WORKSPACE_PATH)
    except Exception as error:
        logger.exception(error)
        return
    # Get the base urls from the config
    baseurls = config.get("http", {}).get("baseurls", {})
    # Reformat the tags, parent and buckets
    tags: List[str] = list(tag)
    parents: List[str] = list(parent)
    buckets: List[str] = list(bucket)
    # Setup and connect to the workflow backend
    logger.info(
        "[bold red]Workflow Run CLI[/bold red]", extra=dict(markup=True, color="green")
    )
    logger.info(f"Bucket   : {buckets}")
    logger.info(f"Function : {function}")
    logger.info(f"Command  : {command}")
    logger.info(f"Mode     : {'Static' if (function or command) else 'Dynamic'}")
    logger.info(f"Lives    : {'infinite' if lives == -1 else lives}")
    logger.info(f"Sleep    : {sleep}s")
    logger.info(f"Log Level: {log_level}")
    logger.info(
        "[bold red]Workspace [/bold red]",
        extra=dict(markup=True, color="green"),
    )
    logger.info(f"Buckets URL : {baseurls.get('buckets')}")
    logger.info(f"Loki    URL : {baseurls.get('loki')}")
    logger.info(f"Prod    URL : {baseurls.get('products')}")
    logger.info(
        "[bold red]Work Filters [/bold red]",
        extra=dict(markup=True, color="green"),
    )
    logger.info(f"Site   : {site}")
    logger.info(f"Tags   : {tags}") if tags else None
    logger.info(f"Parents: {parents}") if parents else None
    logger.info(
        "[bold red]Execution Environment [/bold red]",
        extra=dict(markup=True, color="green"),
    )
    logger.info(f"Operating System: {platform.system()}")
    logger.info(f"Python Version  : {platform.python_version()}")
    logger.info(f"Python Compiler : {platform.python_compiler()}")
    logger.info(f"Virtualization  : {container.virtualization()}")
    logger.info(
        "[bold red]Backend Checks [/bold red]",
        extra=dict(markup=True, color="green"),
    )
    loki_status = add_loki_handler(logger, baseurls.get("loki"), config)
    logger.info(f"Loki Logs: {'✅' if loki_status else '❌'}")

    try:
        HTTPContext(backends=["buckets"]).buckets.info()
        logger.info("Buckets  : ✅")
    except Exception as error:
        logger.exception(error)
        return
    # Check if the function value provided is valid
    if function:
        validate.function(function)
        logger.info("Function : ✅")

    try:
        logger.info(
            "[bold]Starting Workflow Lifecycle[/bold]",
            extra=dict(markup=True, color="green"),
        )
        console = Console(force_terminal=True, tab_size=4)
        tty: bool = stdout.isatty() or stderr.isatty()
        with console.status(
            status="",
            spinner="aesthetic" if tty else "dots",
            spinner_style="bold green",
            refresh_per_second=10 if tty else 0.1,
        ):
            lifecycle(
                buckets,
                function,
                lives,
                sleep,
                site,
                tags,
                parents,
                config,
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
    lifetime: int,
    sleep_time: int,
    site: str,
    tags: List[str],
    parents: List[str],
    config: Dict[str, Any],
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
    while lifetime != 0 and not exit.is_set():
        attempt(buckets, function, site, tags, parents, config)
        lifetime -= 1
        logger.debug(f"sleeping: {sleep_time}s")
        exit.wait(sleep_time)
        logger.debug(f"awake: {sleep_time}s")


def attempt(
    buckets: List[str],
    function: Optional[str],
    site: str,
    tags: List[str],
    parents: List[str],
    config: Dict[str, Any],
) -> bool:
    """Attempt to perform work.

    Args:
        buckets (str): Name of the buckets to perform work from.
        function (Optional[str]): Static function to perform work.
        base_url (str): URL of the workflow backend.
        site (str): Site to filter work by.
        tags (Optional[List[str]]): Tags to filter work by.
        parent (Optional[str]): Parent pipeline to filter work by.

    Returns:
        bool: True if work was performed, False otherwise.
    """
    mode: str = "dynamic"
    work: Optional[Work] = None
    command: Optional[List[str]] = None
    user_func: Optional[Callable[..., Any]] = None
    status: bool = False

    try:
        if function:
            mode = "static"
            user_func = validate.function(function)
        else:
            mode = "dynamic"
            user_func = None

        # Get work from the workflow backend
        try:
            work = Work.withdraw(pipeline=buckets, site=site, tags=tags, parent=parents)
        except Exception as error:
            logger.exception(error)

        if work:
            # Set the work id for the logger
            set_tag(work.id)  # type: ignore
            logger.info("work retrieved: ✅")
            logger.debug(f"work payload  : {work.payload}")
            if mode == "dynamic":
                # Get the user function from the work object
                function = work.function
                command = work.command
                assert command or function, "neither function or command provided"

            # Get the user function from the work object dynamically
            if function:
                user_func = validate.function(function)
                work = execute.function(user_func, work)

            # If we have a valid command, execute it
            if command:
                validate.command(command[0])
                work = execute.command(command, work)
            if int(work.timeout) + int(work.start) < time.time():  # type: ignore
                raise TimeoutError("work timed out")
            archive.run(work, config)
            status = True
    except Exception as error:
        logger.exception(error)
        work.status = "failure"  # type: ignore
    finally:
        if work:
            product_url = config.get("http", {}).get("baseurls", {}).get("products", "")
            if any(work.notify.slack.model_dump().values()) and work.products:
                work.products = [
                    f"<{product_url}{product}|{product}>" for product in work.products
                ]
            if any(work.notify.slack.model_dump().values()) and work.plots:
                work.plots = [f"<{product_url}{plot}|{plot}>" for plot in work.plots]
            work.update()  # type: ignore
            logger.info("work completed: ✅")
        unset_tag()
        return status


if __name__ == "__main__":
    run()
