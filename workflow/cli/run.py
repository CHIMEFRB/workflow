"""Fetch and process Work using any method compatible with Tasks API."""

import platform
import signal
import time
from threading import Event
from typing import Any, Callable, Dict, List, Optional, Tuple

import click
import requests
from rich.console import Console

from workflow import DEFAULT_WORKSPACE_PATH
from workflow.definitions.work import Work
from workflow.lifecycle import archive, container, execute, validate
from workflow.utils import read as reader
from workflow.utils.logger import add_loki_handler, get_logger, set_tag, unset_tag

logger = get_logger("workflow.cli")


@click.command("run", short_help="Fetch & Perform Work.")
@click.argument("buckets", type=str, required=True)
@click.option(
    "-s",
    "--site",
    type=str,
    required=True,
    show_default=True,
    help="filter work by site.",
)
@click.option(
    "-t",
    "--tag",
    type=str,
    multiple=True,
    required=False,
    default=None,
    show_default=True,
    help="filter work by tag.",
)
@click.option(
    "-p",
    "--parent",
    type=str,
    required=False,
    default=None,
    show_default=True,
    help="filter work by parent.",
)
@click.option(
    "-f",
    "--function",
    type=str,
    required=False,
    default=None,
    show_default=True,
    help="overload function to execute.",
)
@click.option(
    "-c",
    "--command",
    type=str,
    required=False,
    default=None,
    show_default=True,
    help="overload command to execute.",
)
@click.option(
    "--lives",
    "-l",
    type=int,
    default=-1,
    show_default=True,
    help="count of work to perform.",
)
@click.option(
    "--sleep",
    type=int,
    default=30,
    show_default=True,
    help="sleep between work attempts.",
)
@click.option(
    "-w",
    "--workspace",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    default=DEFAULT_WORKSPACE_PATH,
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
    bucket: str,
    site: str,
    tag: Tuple[str],
    parent: Optional[str],
    function: str,
    command: str,
    lives: int,
    sleep: int,
    workspace: str,
    log_level: str,
):
    """Fetch & Perform Work."""
    # Set logging level
    logger.root.setLevel(log_level)
    logger.root.handlers[0].setLevel(log_level)
    config = reader.workspace(workspace)
    baseurls = config.get("http", {}).get("baseurls", {})
    buckets_url = baseurls.get("buckets", None)
    loki_url = baseurls.get("loki", None)
    products_url = baseurls.get("products", None)

    # Reformate tag to be a list of strings
    tags: List[str] = list(tag)
    # Setup and connect to the workflow backend
    logger.info("[bold]Workflow Run CLI[/bold]", extra=dict(markup=True, color="green"))
    logger.info(f"Bucket   : {bucket}")
    logger.info(f"Function : {function}")
    logger.info(f"Command  : {command}")
    logger.info(f"Mode     : {'Static' if (function or command) else 'Dynamic'}")
    # Print inifinity symbol if lifetime is -1, otherwise print lifetime
    logger.info(f"Lives    : {'infinite' if lives == -1 else lives}")
    logger.info(f"Sleep    : {sleep}s")
    logger.info(f"Log Level: {log_level}")
    logger.info(f"Base URL : {buckets_url}")
    logger.info(f"Loki URL : {loki_url}")
    logger.info(f"Prod URL : {products_url}")
    logger.info(
        "[bold red]Work Filters [/bold red]",
        extra=dict(markup=True, color="green"),
    )
    logger.info(f"Site: {site}")
    if tags:
        logger.info(f"Tags: {tags}")
    if parent:
        logger.info(f"Parent Pipeline: {parent}")
    logger.info(
        "[bold]Execution Environment [/bold]",
        extra=dict(markup=True, color="green"),
    )
    logger.info(f"Operating System: {platform.system()}")
    logger.info(f"Python Version  : {platform.python_version()}")
    logger.info(f"Python Compiler : {platform.python_compiler()}")
    logger.info(f"Virtualization  : {container.virtualization()}")
    logger.info(
        "[bold]Configuration Checks [/bold]",
        extra=dict(markup=True, color="green"),
    )
    loki_status = add_loki_handler(logger, loki_url, config)
    logger.info(f"Loki Logs: {'✅' if loki_status else '❌'}")

    try:
        requests.get(buckets_url).headers
        logger.info("Base URL : ✅")
        logger.debug(f"base_url: {buckets_url}")
    except Exception as error:
        logger.error(error)
        raise click.ClickException("unable to connect to workflow backend")

    # Check if the function value provided is valid
    if function:
        validate.function(function)
        logger.info("Function : ✅")

    try:
        logger.info(
            "[bold]Starting Workflow Lifecycle[/bold]",
            extra=dict(markup=True, color="green"),
        )
        slowdown: float = 1.0
        if container.virtualization():
            slowdown = 1000.0
        console = Console(force_terminal=True, tab_size=4)
        with console.status(
            status="",
            spinner="toggle2",
            spinner_style="bold green",
            refresh_per_second=1,
            speed=1 / slowdown,
        ):
            lifecycle(
                bucket, function, lives, sleep, site, tags, parent, buckets_url, config
            )
    except Exception as error:
        logger.exception(error)
    finally:
        logger.info(
            "[bold]Workflow Lifecycle Complete[/bold]",
            extra=dict(markup=True, color="green"),
        )


def lifecycle(
    bucket: str,
    function: Optional[str],
    lifetime: int,
    sleep_time: int,
    site: str,
    tags: List[str],
    parent: Optional[str],
    base_url: str,
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
        attempt(bucket, function, base_url, site, tags, parent, config)
        lifetime -= 1
        logger.debug(f"sleeping: {sleep_time}s")
        exit.wait(sleep_time)
        logger.debug(f"awake: {sleep_time}s")


def attempt(
    bucket: str,
    function: Optional[str],
    base_url: str,
    site: str,
    tags: Optional[List[str]],
    parent: Optional[str],
    config: Dict[str, Any],
) -> bool:
    """Attempt to perform work.

    Args:
        bucket (str): Name of the bucket to perform work from.
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
            work = Work.withdraw(pipeline=bucket, site=site, tags=tags, parent=parent)
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
            if any(work.notify.slack.dict().values()) and work.products:
                work.products = [
                    f"<{product_url}{product}|{product}>" for product in work.products
                ]
            if any(work.notify.slack.dict().values()) and work.plots:
                work.plots = [f"<{product_url}{plot}|{plot}>" for plot in work.plots]
            work.update()  # type: ignore
            logger.info("work completed: ✅")
        unset_tag()
        return status


if __name__ == "__main__":
    run()
