"""Fetch and process Work using any method compatible with Tasks API."""


import signal
import time
from threading import Event
from typing import Any, Callable, Dict, List, Optional

import click
import requests
from rich.console import Console

from chime_frb_api import get_logger
from chime_frb_api.core.logger import set_tag, unset_tag
from chime_frb_api.workflow import Work
from chime_frb_api.workflow.lifecycle import archive, execute, validate

BASE_URLS: List[str] = ["http://frb-vsop.chime:8004", "https://frb.chimenet.ca/buckets"]

logger = get_logger("workflow")


@click.command("run", short_help="Perform work.")
@click.argument("bucket", type=str, required=True)
@click.argument(
    "function",
    type=str,
    required=False,
    default=None,
)
@click.option(
    "-c",
    "--command",
    type=str,
    required=False,
    default=None,
    show_default=True,
    help="command to perform, e.g. `ls -l`",
)
@click.option(
    "-l",
    "--lifetime",
    type=int,
    default=-1,
    show_default=True,
    help="number of works to perform. -1 for infinite.",
)
@click.option(
    "-s",
    "--sleep-time",
    type=int,
    default=30,
    show_default=True,
    help="time to sleep between work attempts.",
)
@click.option(
    "-b",
    "--base-urls",
    multiple=True,
    default=BASE_URLS,
    show_default=True,
    help="url(s) of the workflow backend.",
)
@click.option(
    "--site",
    type=click.Choice(
        ["chime", "allenby", "kko", "gbo", "hco", "aro", "canfar", "cedar", "local"]
    ),
    default="chime",
    show_default=True,
    help="filter work by site.",
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
    function: str,
    command: str,
    lifetime: int,
    sleep_time: int,
    base_urls: List[str],
    site: str,
    log_level: str,
):
    """Perform work retrieved from the workflow buckets."""
    # Set logging level
    logger.root.setLevel(log_level)
    logger.root.handlers[0].setLevel(log_level)
    base_url: Optional[str] = None
    # Setup and connect to the workflow backend
    logger.info("[bold]Workflow Run CLI[/bold]", extra=dict(markup=True, color="green"))
    logger.info(f"Bucket   : {bucket}")
    logger.info(f"Function : {function}")
    logger.info(f"Command  : {command}")
    logger.info(f"Mode     : {'Static' if (function or command) else 'Dynamic'}")
    # Print inifinity symbol if lifetime is -1, otherwise print lifetime
    logger.info(f"Lifetime : {'infinite' if lifetime == -1 else lifetime}")
    logger.info(f"Sleep    : {sleep_time}s")
    logger.info(f"Work Site: {site}")
    logger.info(f"Base URLs: {base_urls}")
    logger.info(f"Log Level: {log_level}")
    logger.info(
        "[bold]Workflow Configuration Check[/bold]",
        extra=dict(markup=True, color="green"),
    )

    for url in base_urls:
        try:
            requests.get(url).headers
            logger.info("Base URLs: ✔️")
            logger.debug(f"url: {url}")
            base_url = url
            break
        except requests.exceptions.RequestException:
            logger.debug(f"unable to connect: {url}")

    if not base_url:
        logger.error("unable to connect to workflow backend.")
        raise RuntimeError("unable to connect to workflow backend")

    # Check if the function value provided is valid
    if function:
        validate.function(function)
        logger.info("Function : ✔️")

    try:
        logger.info(
            "[bold]Starting Workflow Lifecycle[/bold]",
            extra=dict(markup=True, color="green"),
        )
        console = Console(force_terminal=True, tab_size=4)
        with console.status(
            status="Running...",
            spinner="arc",
            spinner_style="bold green",
        ):
            lifecycle(bucket, function, lifetime, sleep_time, site, base_url)
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
    base_url: str,
):
    """Run the workflow lifecycle."""
    # Start the exit event
    exit = Event()

    # Get any stop, kill, or terminate signals and set the exit event
    def quit(signo: int, _):
        """Handle terminal signals."""
        logger.critical(f"Received terminal signal {signo}. Exiting...")
        exit.set()

    # Register the quit function to handle the signals
    for sig in ("TERM", "HUP", "INT"):
        signal.signal(getattr(signal, "SIG" + sig), quit)

    # Run the lifecycle until the exit event is set or the lifetime is reached
    while lifetime != 0 and not exit.is_set():
        attempt(bucket, function, base_url, site)
        lifetime -= 1
        logger.debug(f"sleeping: {sleep_time}s")
        exit.wait(sleep_time)
        logger.debug(f"awake: {sleep_time}s")


def attempt(bucket: str, function: Optional[str], base_url: str, site: str) -> bool:
    """Attempt to perform work.

    Args:
        bucket (str): Name of the bucket to perform work from.
        function (Optional[str]): Static function to perform work.
        base_url (str): URL of the workflow backend.
        site (str): Site to filter work by.

    Returns:
        bool: True if work was performed, False otherwise.
    """
    kwargs: Dict[str, Any] = {"base_url": base_url}
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
            work = Work.withdraw(pipeline=bucket, site=site, **kwargs)
        except Exception as error:
            logger.exception(error)

        if work:
            # Set the work id for the logger
            set_tag(work.id)  # type: ignore
            logger.info("work retrieved: ✔️")
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
            archive.run(work)
            status = True
    except Exception as error:
        logger.exception(error)
        work.status = "failure"  # type: ignore
    finally:
        if work:
            work.update(**kwargs)  # type: ignore
            logger.info("work completed: ✔️")
        unset_tag()
        return status


if __name__ == "__main__":
    run()
