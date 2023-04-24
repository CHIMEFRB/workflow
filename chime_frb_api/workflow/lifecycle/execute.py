"""Execute the work function or command."""
import ast
import subprocess
import time
from typing import Any, Callable, Dict, List, Optional

import click
from mergedeep import merge

from chime_frb_api import get_logger
from chime_frb_api.workflow import Work

logger = get_logger("workflow")


def function(user_func: Callable[..., Any], work: Work) -> Work:
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
        logger.debug("click cli: ✅")
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
        logger.debug(f"results : {results}")
        logger.debug(f"products: {products}")
        logger.debug(f"plots   : {plots}")
        if results:
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


def command(command: List[str], work: Work) -> Work:
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
    except Exception as error:
        work.status = "failure"
        logger.exception(error)
    finally:
        end = time.time()
        work.stop = end
        logger.info(f"execution time: {end - start:.2f}s")
        return work
