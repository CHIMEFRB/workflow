"""Execute the work function or command."""

import subprocess
import time
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import click

from workflow.definitions.work import Work
from workflow.lifecycle import configure
from workflow.utils import validate
from workflow.utils.logger import get_logger

logger = get_logger("workflow.lifecycle.execute")

Outcome = Union[Dict[str, Any], Tuple[Dict[str, Any], List[str], List[str]], Any, None]


def function(work: Work) -> Work:
    """Execute a Python function.

    Args:
        func (Callable[..., Any]): Python function
        work (Work): The work object

    Returns:
        Work: The work object
    """
    logger.debug(f"executing func: {work.function}")
    start = time.time()
    outcome: Outcome = None
    results: Optional[Dict[str, Any]] = None
    products: Optional[List[str]] = None
    plots: Optional[List[str]] = None
    try:
        assert isinstance(work.function, str), "missing function to execute"
        func: Callable[..., Any] = validate.function(work.function)
        arguments: List[str] = []
        # Configure default values for the function
        work = configure.defaults(func, work)
        # Paramters to execute the function with
        parameters: Dict[str, Any] = work.parameters or {}

        if isinstance(func, click.Command):
            arguments = configure.arguments(parameters)
            logger.info(
                f"executing: {func.name}.main(args={arguments}, standalone_mode=False)"
            )
            outcome = func.main(args=arguments, standalone_mode=False)
        else:
            logger.info(
                f"executing as python function: {func.__name__}(**{work.parameters})"
            )
            outcome = func(**parameters)
        logger.info(f"func call outcome: {outcome}")
        results, products, plots = validate.outcome(outcome)
        logger.debug(f"results: {results}")
        logger.debug(f"products: {products}")
        logger.debug(f"plots: {plots}")
        # * Merge work object with results, products, and plots
        if results and not work.results:
            work.results = results
        if results and work.results:
            work.results = {**work.results, **results}
        if products:
            work.products = (work.products or []) + products
        if plots:
            work.plots = (work.plots or []) + plots
        work = validate.size(work)
        work.status = "success"
    except Exception as error:
        work.status = "failure"
        logger.error(error)
    finally:
        end = time.time()
        work.stop = end
        logger.info(f"execution time: {end - start:.2f}s")
        return work


def command(work: Work) -> Work:
    """Execute a command.

    Args:
        command (List[str]): Command to execute
        work (Work): Work object

    Returns:
        Work: Work object
    """
    # Execute command in a subprocess with stdout and stderr redirected to PIPE
    # and timeout of work.timeout
    logger.debug(f"executing command: {work.command}")
    start = time.time()
    try:
        assert isinstance(work.command, list), "missing command to execute"
        validate.command(work.command[0])
        process = subprocess.run(
            work.command,
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
        if not (work.results or work.products or work.plots):
            work.results = {
                "args": process.args,
                "stdout": stdout,
                "stderr": stderr,
                "returncode": process.returncode,
            }
        # * Check if results are less than 4MB
        validate.size(work)
        work.status = "success"
    except Exception as error:
        work.status = "failure"
        logger.exception(error)
    finally:
        end = time.time()
        work.stop = end
        logger.info(f"execution time: {end - start:.2f}s")
        return work
