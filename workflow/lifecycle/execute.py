"""Execute the work function or command."""

import ast
import subprocess
import time
from sys import getsizeof
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import click
from mergedeep import merge  # type: ignore

from workflow.definitions.work import Work
from workflow.utils.logger import get_logger

logger = get_logger("workflow.lifecycle.execute")

Outcome = Union[Dict[str, Any], Tuple[Dict[str, Any], List[str], List[str]]]


def function(func: Callable[..., Any], work: Work) -> Work:
    """Execute a Python function.

    Args:
        func (Callable[..., Any]): Python function
        work (Work): The work object

    Returns:
        Work: The work object
    """
    # Execute the function
    logger.debug(f"executing func: {func}")
    func, parameters = gather(func, work)
    logger.info(f"executing: {func.__name__}(**{parameters})")
    start = time.time()
    outcome: Optional[Outcome] = None
    results: Optional[Dict[str, Any]] = None
    products: Optional[List[str]] = None
    plots: Optional[List[str]] = None
    try:
        outcome = func(**parameters)
        # * If the outcome is a dict, assume it is results
        if isinstance(outcome, dict):
            results = outcome
        # * If the outcome is tuple of len 3, assume it is results, products, plots
        elif isinstance(outcome, tuple) and len(outcome) == 3:
            results, products, plots = outcome
        else:
            logger.warning(f"could not parse work outcome: {outcome}")
            logger.error(f"outcome ignored for work: {work.id}")
        logger.debug(f"results: {results}")
        logger.debug(f"products: {products}")
        logger.debug(f"plots: {plots}")
        # * Merge function output with work object
        if results:
            # * Check if results are less than 4MB
            if getsizeof(results) > 4_000_000:
                logger.error(
                    f"results size {getsizeof(results)/1000000:.2f}MB exceeds 4MB"
                )
                logger.error("results not mapped to work object")
                results = None
            work.results = merge(work.results or {}, results)  # type: ignore
        if products:
            work.products = (work.products or []) + products
        if plots:
            work.plots = (work.plots or []) + plots
        work.status = "success"
    except Exception as error:
        work.status = "failure"
        logger.exception(error)
    finally:
        end = time.time()
        work.stop = end
        logger.info(f"execution time: {end - start:.2f}s")
        return work


def gather(
    func: Callable[..., Any], work: Work
) -> Tuple[Callable[..., Any], Dict[str, Any]]:
    """Gather the parameters for the user function.

    Args:
        func (Callable[..., Any]): User function
        work (Work): Work object

    Returns:
        Tuple[Callable[..., Any], Dict[str, Any]]:
            Tuple of user function and parameters
    """
    defaults: Dict[Any, Any] = {}
    if isinstance(func, click.Command):
        # Get default options from the click command
        known: List[Any] = list(work.parameters.keys()) if work.parameters else []
        for parameter in func.params:
            if parameter.name not in known:  # type: ignore
                defaults[parameter.name] = parameter.default
        if defaults:
            logger.debug(f"click cli defaults: {defaults}")
        func = func.callback  # type: ignore
    # If work.parameters is empty, merge an empty dict with the defaults
    # Otherwise, merge the work.parameters with the defaults
    parameters: Dict[str, Any] = {}
    if work.parameters:
        parameters = {**work.parameters, **defaults}
    else:
        parameters = defaults
    return func, parameters


def command(command: List[str], work: Work) -> Work:
    """Execute a command.

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
        # Convert stdout and stderr to strings
        stdout = process.stdout.decode("utf-8").splitlines()
        stderr = process.stderr.decode("utf-8").splitlines()
        # Convert last line of stdout to a Tuple
        response: Any = None
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
        # * Check if results are less than 4MB
        size: int = getsizeof(work.results)  # type: ignore
        if size > 4_000_000:
            logger.error(f"results size {size:.2f}MB exceeds 4MB")
            logger.error("results not mapped to work object")
            work.results = None
        work.status = "success"
    except Exception as error:
        work.status = "failure"
        logger.exception(error)
    finally:
        end = time.time()
        work.stop = end
        logger.info(f"execution time: {end - start:.2f}s")
        return work
