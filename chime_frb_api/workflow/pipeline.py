"""Fetch and process Work using any method compatible with Tasks API."""

import logging
import time
from importlib import import_module
from multiprocessing import Pipe, Process
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
):
    """Run workflow pipeline.

    Withdraws Work object from appropriate bucket/pipeline,
    attempts to execute "func(**work.parameters)",
    then updates results and success/failure status.

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
    logger.info("Connecting to the workflow backend...")
    base_url: Optional[str] = None
    for url in base_urls:
        try:
            requests.get(url).headers
            logger.info(f"Connected to {url}")
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
        work = attempt_work(pipeline, function, base_url, site)
        if work is None:
            logger.debug(f"No work found, sleeping for {sleep_time} seconds")
            time.sleep(sleep_time)
        else:
            lifetime -= 1

    return


def attempt_work(
    name: str, user_func: FUNC_TYPE, base_url: str, site: str
) -> Optional["Work"]:
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
        Optional[Work]: Work object if successful, None otherwise.
    """
    kwargs: Dict[str, Any] = {"base_url": base_url}
    work: Optional["Work"] = None
    try:
        work = Work.withdraw(pipeline=name, site=site, **kwargs)
    except requests.RequestException as error:
        logger.error(error)
        logger.error("Failed to withdraw work, retrying in 10 seconds")
    finally:
        if not work:
            return None

    def apply_func(connection, func, **kwargs):
        """Executes in child process & pipes results back."""
        if isinstance(func, click.Command):
            for param in func.params:
                kwargs.setdefault(param.name, param.default)
            func = func.callback
        connection.send(func(**kwargs))
        connection.close()

    receiver, sender = Pipe()  # to communicate with child

    process = Process(
        target=apply_func,
        args=(sender, user_func),
        kwargs=work.parameters or {},
    )

    process.start()
    process.join(work.timeout if work.timeout > 0 else None)

    if process.is_alive():
        process.terminate()

    output = receiver.recv() if receiver.poll() else None

    if output and process.exitcode == 0:
        try:
            results, products, plots = output
            work.results = results
            work.products = products
            work.plots = plots
            work.status = "success"
        except (TypeError, ValueError) as error:
            logger.error(error)
            logger.error("User function must return (results, products, plots)")
            work.status = "failure"
    else:
        work.status = "failure"

    # Log possible outcomes
    if process.exitcode == 0 and work.status == "failure":
        logger.error("user func output doesn't match chime/frb standard")
    elif process.exitcode is None:
        logger.error("user func timed out")
    elif process.exitcode != 0:
        logger.error("user func raised an error")
    else:
        logger.info("user func was successful")

    work.update()
    return work


if __name__ == "__main__":
    run()
