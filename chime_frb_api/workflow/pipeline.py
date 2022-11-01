"""Fetch and process Work using any method compatible with Tasks API."""

import logging
import time
from importlib import import_module
from typing import Any, Callable, Dict, List, Optional, Tuple

import click
import requests

from chime_frb_api.workflow import Work

BASE_URLS: List[str] = ["http://frb-vsop.chime:8001", "https://frb.chimenet.ca/buckets"]

# Configure logger
LOGGING_FORMAT = "[%(asctime)s] %(levelname)s %(message)s"
logging.basicConfig(format=LOGGING_FORMAT, level=logging.INFO)
logger = logging.getLogger(__name__)

FUNC_TYPE = Callable[..., Tuple[Dict[str, Any], List[str], List[str]]]


@click.command("run", short_help="Execute user function on Work objects")
@click.argument("pipeline", type=str)
@click.argument("func", type=str)
@click.option(
    "--lifetime",
    type=int,
    default=-1,
    show_default=True,
    help="Work to do before exiting, -1 for infinite.",
)
@click.option(
    "--sleep-time",
    type=int,
    default=10,
    show_default=True,
    help="Seconds to sleep between fetch attempts.",
)
@click.option(
    "--base-urls",
    multiple=True,
    default=BASE_URLS,
    show_default=True,
    help="Workflow backend url(s).",
)
@click.option(
    "--site",
    type=click.Choice(
        ["chime", "allenby", "gbo", "hatcreek", "canfar", "cedar", "local"]
    ),
    default="chime",
    show_default=True,
    help="Site where work is being performed.",
)
@click.option(
    "-l",
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    default="INFO",
    show_default=True,
    help="Logging level to use.",
)
def run(
    pipeline: str,
    func: str,
    lifetime: int,
    sleep_time: int,
    base_urls: List[str],
    site: str,
    log_level: str,
) -> None:
    """Run a workflow pipeline.

    Following Actions are performed:
        1. Withdraws `Work` from appropriate pipeline.
        2. Attempt to execute `func(**work.parameters)` in a child process.
        3. Updates results, plots, products and status.

    Args:
        pipeline (str): pipeline/bucket that work objects will be fetched from
        func (str): module.function to be executed on the work object
        lifetime (int): number of work objects to be processed before exiting
        sleep_time (int): number of seconds to sleep between fetch attempts
        base_urls (List[str]): url(s) of the workflow backend
        site (str): site for which work is being performed
        log_level (str): logging level to use

    Raises:
        RuntimeError: If we cannot run workflow processing.
        TypeError: If we cannot import the user function.
    """
    # Set logging level
    logger.setLevel(log_level)
    logger.info("Connecting to workflow backend...")
    base_url: Optional[str] = None
    for url in base_urls:
        try:
            requests.get(url).headers
            logger.info(f"Connected @ {url}")
            base_url = url
        except requests.exceptions.RequestException:
            logger.warning(f"Unable to connect to {url}")

    if not base_url:
        logger.error("Unable to connect to any workflow backend")
        raise RuntimeError("Unable to connect to any workflow backend")

    # Always print the logging level in the log message
    logger.info("Starting pipeline %s with func %s", pipeline, func)
    try:
        # Name of the module containing the user function
        module_name, func_name = func.rsplit(".", 1)
        logger.debug(f"Module  : {module_name}")
        logger.debug(f"Function: {func_name}")
        module = import_module(module_name)
        function = getattr(module, func_name)
        logger.debug(f"Successfully imported {func}")
        # Check if the function is callable
        if not callable(function):
            raise TypeError(f"{func} is not callable")
    except (ImportError, AttributeError, TypeError) as error:
        logger.error(error)
        logger.error("Imports failed (use 'package.module.function' format)")
        return

    while lifetime != 0:
        done = attempt_work(pipeline, function, base_url, site)
        if not done:
            logger.debug("Failed or No work performed.")
        else:
            logger.debug("Successfully performed work.")
            lifetime -= 1
        logger.debug(f"Sleeping for {sleep_time} seconds")
        time.sleep(sleep_time)
    return None


def attempt_work(name: str, user_func: FUNC_TYPE, base_url: str, site: str) -> bool:
    """Attempt pipeline work.

    Fetches 'work' object from appropriate pipeline/bucket, then calls
    user_func(**work.parameters) in a child process, terminating after
    work.timeout (s). Sets results and success/failure status in work
    object, and then calls work.update().

    Args:
        name (str): Specifies the pipeline/bucket that work objects will be fetched from
            (e.g. dm-pipeline, fitburst, fitburst-some-dev-branch).
        user_func (FUNC_TYPE): Function returns (results, products, plots) tuple.
            'results' is a generic dictionary, while 'products' and 'plots'
            are lists of paths. Executed as user_func(**work.parameters).
        base_url (str): url of the workflow backend
        site (str): site where work is processed (default chime). Options are chime,
        allenby, gbo, hatcreek, canfar, cedar, local.

    Returns:
        bool: If work was successful.
    """
    kwargs: Dict[str, Any] = {"base_url": base_url}
    work: Optional["Work"] = None
    try:
        work = Work.withdraw(pipeline=name, site=site, **kwargs)
    except requests.RequestException as error:
        logger.error(error)
        logger.error("failed to withdraw work, will retry soon...")
    finally:
        if not work:
            return False
        else:
            logger.info("Successfully withdrew work")
            logger.debug(f"Withdrew work {work.payload}")
            logger.info("Starting to perform work")

    # If the function is a click command, gather all the default options
    defaults: Dict[Any, Any] = {}
    if isinstance(user_func, click.Command):
        logger.debug("user function is a click cli command")
        logger.debug("gathering default options not specified in work.parameters")
        # Get default options from the click command
        for parameter in user_func.params:
            if parameter.name not in work.parameters.keys():  # type: ignore
                defaults[parameter.name] = parameter.default
        logger.debug(f"CLI Defaults: {defaults}")
        user_func = user_func.callback  # type: ignore

    # Merge the defaults with the work parameters
    parameters: Dict[Any, Any] = {**defaults, **work.parameters}  # type: ignore

    # Execute the user function
    try:
        logger.debug(f"Executing {user_func.__name__}(**{parameters})")
        start = time.time()
        results, products, plots = user_func(**parameters)
        end = time.time()
        logger.debug(f"Execution time: {end - start:.2f} s")
        logger.debug(f"Results: {results}")
        logger.debug(f"Products: {products}")
        logger.debug(f"Plots: {plots}")
        work.results = results
        work.products = products
        work.plots = plots
        work.status = "success"
        if int(work.timeout) + int(work.creation) < time.time():  # type: ignore
            logger.warning("even though work was successful, it timed out")
            logger.warning("setting status to failure")
            work.status = "failure"
    except (TypeError, ValueError) as error:
        logger.error(error)
        logger.error("user function must return (results, products, plots)")
        work.status = "failure"
    except Exception as error:
        logger.error("failed to execute user function")
        logger.error(error)
        work.status = "failure"
    finally:
        try:
            logger.debug(f"Updating work {work.payload}")
            work.update(**kwargs)
        except requests.RequestException as error:
            logger.error(error)
            logger.error("failed to update work, will retry soon...")
            return False
    return True


if __name__ == "__main__":
    run()
