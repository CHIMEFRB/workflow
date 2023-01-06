"""Fetch and process Work using any method compatible with Tasks API."""

import logging
import time
from importlib import import_module
from typing import Any, Callable, Dict, List, Optional, Tuple

import click
import requests

from chime_frb_api.workflow import Work

BASE_URLS: List[str] = ["http://frb-vsop.chime:8004", "https://frb.chimenet.ca/buckets"]
# Checkmark & Cross and other Unicode characters
CHECKMARK = "\u2713"
CROSS = "\u2717"
CIRCLE = "\u25CB"
WARNING_SIGN = "\u26A0"

# Configure logger
LOGGING_FORMAT = (
    "[%(asctime)s] %(levelname)s %(name)s %(lineno)d %(funcName)s: %(message)s"
)
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
    help="Works to perform before exiting, -1 for infinite.",
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
) -> bool:
    r"""Run a workflow pipeline.

    Performs the following steps: \n
    \t1. Withdraws `Work` from appropriate pipeline.\t\t\t\t
    \t2. Attempt to execute `func(**work.parameters)`.\t\t\t\t
    \t3. Updates results, plots, products and status.
    """
    # Set logging level
    logger.setLevel(log_level)
    base_url: Optional[str] = None
    # Setup and connect to the workflow backend
    logger.info("=" * 80)
    logger.info("Workflow Backend")
    for url in base_urls:
        try:
            requests.get(url).headers
            logger.info(f"Connection: {CHECKMARK}")
            logger.debug(f"URL: {url}")
            base_url = url
            break
        except requests.exceptions.RequestException:
            logger.debug(f"Unable to connect to {url}")

    if not base_url:
        logger.error(f"Connection: {CROSS}")
        logger.debug("Unable to connect to any of the provided base_urls.")
        logger.debug(f"Attempted URLS: {base_urls}")
        raise RuntimeError("Unable to connect to any workflow backend")

    logger.info("=" * 80)
    logger.info("Pipeline Configuration")

    # Always print the logging level in the log message
    logger.info(f"Pipeline: {pipeline}")
    logger.info(f"Function: {func}")
    try:
        # Name of the module containing the user function
        module_name, func_name = func.rsplit(".", 1)
        module = import_module(module_name)
        function = getattr(module, func_name)
        logger.info(f"Imports: {CHECKMARK}")
        # Check if the function is callable
        if not callable(function):
            raise TypeError(f"{func} is not callable")
        logger.info(f"Callable: {CHECKMARK}")
    except ImportError as error:
        logger.error(f"Imports: {CROSS}")
        logger.debug(error)
        raise error
    except (AttributeError, TypeError) as error:
        logger.error(f"Function: {CROSS}")
        logger.error(error)
        raise error

    logger.info("=" * 80)
    logger.info("Work Lifecycle")
    logger.info("=" * 80)
    while lifetime != 0:
        done = attempt_work(pipeline, function, base_url, site)
        logger.info(f"Work Performed: {CHECKMARK if done else CROSS}")
        lifetime -= 1
        logger.debug(f"Sleeping: {sleep_time} seconds")
        time.sleep(sleep_time)
    return True


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
        logger.info(f"Work Withdrawn: {CHECKMARK if work else CIRCLE}")
    except Exception as error:
        logger.error(f"Work Withdrawn: {CROSS}")
        logger.error(error)
    finally:
        if not work:
            return False
        else:
            logger.debug(f"Work: {work.payload}")

    # If the function is a click command, gather all the default options
    defaults: Dict[Any, Any] = {}
    if isinstance(user_func, click.Command):
        logger.info(f"Click CLI Detected: {CHECKMARK}")
        logger.debug("Gathering CLI Defaults")
        # Get default options from the click command
        known: List[Any] = list(work.parameters.keys()) if work.parameters else []
        for parameter in user_func.params:
            if parameter.name not in known:  # type: ignore
                defaults[parameter.name] = parameter.default
        if defaults:
            logger.info(f"CLI Defaults: {CHECKMARK}")
            logger.debug(f"CLI Defaults: {defaults}")
        user_func = user_func.callback  # type: ignore
    else:
        logger.info(f"CLI Detected: {CIRCLE}")

    # If work.parameters is empty, merge an empty dict with the defaults
    # Otherwise, merge the work.parameters with the defaults
    parameters: Dict[str, Any] = {}
    if work.parameters:
        parameters = {**work.parameters, **defaults}
    else:
        parameters = defaults
    logger.info(f"Parameters: {CHECKMARK}")
    logger.debug(f"Parameters: {parameters}")

    # Execute the user function
    try:
        logger.info(f"Work Started: {CHECKMARK}")
        logger.debug(f"Executing {user_func.__name__}(**{parameters})")
        start = time.time()
        results, products, plots = user_func(**parameters)
        logger.info(f"Work Completed: {CHECKMARK}")
        end = time.time()
        logger.info(f"Execution Time: {end - start:.2f} s")
        logger.debug(f"Results: {results}")
        logger.debug(f"Products: {products}")
        logger.debug(f"Plots: {plots}")
        work.results = results
        work.products = products
        work.plots = plots
        logger.info(f"Work Results: {CHECKMARK}")
        work.status = "success"
        logger.info(f"Work Status: {CHECKMARK}")
        if int(work.timeout) + int(work.creation) < time.time():  # type: ignore
            logger.warning("even though work was successful, it timed out")
            logger.warning("setting status to failure")
            work.status = "failure"
    except (TypeError, ValueError) as error:
        logger.error(f"Work Results: {CROSS}")
        logger.error(error)
        logger.error("user function must return (results, products, plots)")
        work.status = "failure"
    except Exception as error:
        logger.error(f"Work Status: {CROSS}")
        logger.error("failed to execute user function")
        logger.error(error)
        work.status = "failure"
    finally:
        try:
            updated: bool = False
            work.stop = time.time()
            logger.debug(f"Updated Work: {work.payload}")
            # Try to update work multiple times
            for _ in range(10):
                try:
                    work.update(**kwargs)
                    logger.info(f"Work Updated: {CHECKMARK}")
                    updated = True
                    break
                except requests.RequestException:
                    logger.debug("retrying work update...")
                    time.sleep(1)
            if not updated:
                logger.error(f"Work Updated: {CROSS}")
                raise RuntimeError("work completed, but failed to update it!!!")
        except Exception as error:
            logger.error(error)
            return False
    return True


if __name__ == "__main__":
    run()
