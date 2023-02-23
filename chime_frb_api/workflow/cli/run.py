"""Fetch and process Work using any method compatible with Tasks API."""


import ast
import subprocess
import time
from importlib import import_module
from typing import Any, Callable, Dict, List, Optional, Tuple

import click
import requests
from rich.console import Console

from chime_frb_api import get_logger
from chime_frb_api.core.logger import set_tag, unset_tag
from chime_frb_api.utils import copy
from chime_frb_api.workflow import Work

FUNC_TYPE = Callable[..., Tuple[Dict[str, Any], List[str], List[str]]]
BASE_URLS: List[str] = ["http://frb-vsop.chime:8004", "https://frb.chimenet.ca/buckets"]
# Checkmark & Cross and other Unicode characters
CHECKMARK = "\u2713"
CROSS = "\u2717"
CIRCLE = "\u25CB"
WARNING_SIGN = "\u26A0"
INIFINITY = "\u221E"

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
    """Perform work retrieved from the workflow backend."""
    # Set logging level
    logger.root.setLevel(log_level)
    logger.root.handlers[0].setLevel(log_level)
    base_url: Optional[str] = None
    # Setup and connect to the workflow backend
    logger.info("=" * 80)
    logger.info("[bold]Workflow Run CLI[/bold]", extra=dict(markup=True, color="green"))
    logger.info(f"Bucket   : {bucket}")
    logger.info(f"Function : {function}")
    logger.info(f"Command  : {command}")
    logger.info(f"Mode     : {'Static' if (function or command) else 'Dynamic'}")
    logger.info(f"Lifetime : {INIFINITY if lifetime == -1 else lifetime}")
    logger.info(f"Sleep    : {sleep_time}s")
    logger.info(f"Work Site: {site}")
    logger.info(f"Base URLs: {base_urls}")
    logger.info(f"Log Level: {log_level}")
    logger.info("=" * 80)
    logger.info(
        "[bold]Workflow Configuration Check[/bold]",
        extra=dict(markup=True, color="green"),
    )
    for url in base_urls:
        try:
            requests.get(url).headers
            logger.info(f"Base URLs: {CHECKMARK}")
            logger.debug(f"url: {url}")
            base_url = url
            break
        except requests.exceptions.RequestException:
            logger.debug(f"unable to connect: {url}")

    if not base_url:
        logger.error(f"Base URLs: {CROSS}")
        logger.error("unable to connect to workflow backend.")
        raise RuntimeError("unable to connect to workflow backend")

    # Check if the function value provided is valid
    if function:
        validate_function(function)
        logger.info(f"Function : {CHECKMARK}")

    try:
        logger.info("=" * 80)
        logger.info(
            "[bold]Starting Workflow Lifecycle[/bold]",
            extra=dict(markup=True, color="green"),
        )
        logger.info("=" * 80)
        console = Console()
        with console.status(
            status=f"[bold]Performing work for {bucket}[/bold]",
            spinner="dots",
            spinner_style="bold green",
        ):
            lifecycle(bucket, function, lifetime, sleep_time, site, base_url)
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received. Exiting...")
    finally:
        logger.info("=" * 80)
        logger.info(
            "[bold]Workflow Lifecycle Complete[/bold]",
            extra=dict(markup=True, color="green"),
        )
        logger.info("=" * 80)


def lifecycle(
    bucket: str,
    function: Optional[str],
    lifetime: int,
    sleep_time: int,
    site: str,
    base_url: str,
):
    """Run the workflow lifecycle."""
    while lifetime != 0:
        attempt(bucket, function, base_url, site)
        lifetime -= 1
        logger.debug(f"sleeping: {sleep_time}s")
        time.sleep(sleep_time)


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
    user_func: Optional[FUNC_TYPE] = None
    status: bool = False

    try:
        if function:
            mode = "static"
            user_func = validate_function(function)
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
            logger.info(f"work retrieved: {CHECKMARK}")
            logger.debug(f"work payload  : {work.payload}")
            if mode == "dynamic":
                # Get the user function from the work object
                function = work.function
                command = work.command
                assert command or function, "neither function or command provided"

            # Get the user function from the work object dynamically
            if function:
                user_func = validate_function(function)
                work = execute_function(user_func, work)

            # If we have a valid command, execute it
            if command:
                work = execute_command(command, work)
            if int(work.timeout) + int(work.start) < time.time():  # type: ignore
                raise TimeoutError("work timed out")
            if work.archive:
                copy.work_products(work)
            status = True
    except Exception as error:
        logger.exception(error)
        work.status = "failure"  # type: ignore
    finally:
        if work:
            work.update(**kwargs)  # type: ignore
            logger.info(f"work completed: {CHECKMARK}")
        unset_tag()
        return status


def execute_function(user_func: FUNC_TYPE, work: Work) -> Work:
    """Execute the user function.

    Args:
        user_func (FUNC_TYPE): Callable function
        work (Work): Work object

    Returns:
        Work: Work object
    """
    # Execute the function
    logger.debug(f"executing user_func: {user_func}")
    defaults: Dict[Any, Any] = {}
    if isinstance(user_func, click.Command):
        logger.debug(f"click cli: {CHECKMARK}")
        # Get default options from the click command
        known: List[Any] = list(work.parameters.keys()) if work.parameters else []
        for parameter in user_func.params:
            if parameter.name not in known:  # type: ignore
                defaults[parameter.name] = parameter.default
        if defaults:
            logger.debug(f"cli defaults: {defaults}")
        user_func = user_func.callback  # type: ignore
    # If work.parameters is empty, merge an empty dict with the defaults
    # Otherwise, merge the work.parameters with the defaults
    parameters: Dict[str, Any] = {}
    if work.parameters:
        parameters = {**work.parameters, **defaults}
    else:
        parameters = defaults
    logger.info(f"executing: {user_func.__name__}(**{parameters})")
    start = time.time()
    try:
        results, products, plots = user_func(**parameters)
        logger.info(f"work complete : {CHECKMARK}")
        logger.debug(f"results : {results}")
        logger.debug(f"products: {products}")
        logger.debug(f"plots   : {plots}")
        work.results = results
        work.products = products
        work.plots = plots
        work.status = "success"
    except Exception as error:
        work.status = "failure"
        logger.exception(error)
    finally:
        end = time.time()
        work.stop = end
        logger.info(f"execution time: {end - start:.2f}s")
        return work


def execute_command(command: List[str], work: Work) -> Work:
    """Execute the command.

    Args:
        command (List[str]): Command to execute
        work (Work): Work object

    Returns:
        Work: Work object
    """
    # Execute command in a subprocess with stdout and stderr redirected to PIPE
    # and timeout of work.timeout
    logger.debug(f"executing command: {command}")
    start = time.time()
    try:
        process = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=work.timeout,
        )
        # Check return code
        process.check_returncode()
        logger.info(f"work complete : {CHECKMARK}")
        # Convert stdout and stderr to strings
        stdout = process.stdout.decode("utf-8").splitlines()
        stderr = process.stderr.decode("utf-8").splitlines()
        # Convert last line of stdout to a Tuple
        response: Optional[Any] = None
        try:
            response = ast.literal_eval(stdout[-1])
        except SyntaxError as error:
            logger.warning(f"could not parse stdout: {error}")
        except IndexError as error:
            logger.exception(error)
        if isinstance(response, tuple):
            if isinstance(response[0], dict):
                work.results = response[0]
            if isinstance(response[1], list):
                work.products = response[1]
            if isinstance(response[2], list):
                work.plots = response[2]
        if isinstance(response, dict):
            work.results = response
        if not (work.results or work.products or work.plots):
            work.results = {
                "args": process.args,
                "stdout": stdout,
                "stderr": stderr,
                "returncode": process.returncode,
            }
        work.status = "success"
        logger.info(f"work complete : {CHECKMARK}")
    except Exception as error:
        work.status = "failure"
        logger.exception(error)
    finally:
        end = time.time()
        work.stop = end
        logger.info(f"execution time: {end - start:.2f}s")
        return work


def validate_function(function: str) -> FUNC_TYPE:
    """Validate the user function.

    Args:
        function (str): Name of the user function.
            Must be in the form of 'module.submodule.function'.

    Raises:
        TypeError: Raised if the function is not callable.
        error: Raised if the function cannot be imported.

    Returns:
        FUNC_TYPE: Callable user function.
    """
    try:
        # Name of the module containing the user function
        module_name, func_name = function.rsplit(".", 1)
        module = import_module(module_name)
        function = getattr(module, func_name)
        # Check if the function is callable
        if not callable(function):
            raise TypeError(f"{function} is not callable")
    except Exception as error:
        logger.exception(error)
        raise error
    return function


if __name__ == "__main__":
    run()
