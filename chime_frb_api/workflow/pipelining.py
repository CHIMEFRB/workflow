""" Pipeline any method to be compatible with Tasks API. """

import logging
from time import sleep
from functools import wraps
from multiprocessing import Process, Pipe
from typing import Callable, Tuple, Dict, Any, List

from .work import Work


# Configure logger
LOGGING_FORMAT = "[%(asctime)s] %(levelname)s %(message)s"
logging.basicConfig(format=LOGGING_FORMAT, level=logging.INFO)
logger = logging.getLogger(__name__)


FUNC_TYPE = Callable[..., Tuple[Dict[str, Any], List[str], List[str]]]


def pipeline(name: str, func: FUNC_TYPE, lifetime: int = -1) -> None:
    """
    Runs user function on work fetched from the appropriate queue (see buckets
    api).  Success/failure are logged and handled; results and dataproduct paths
    are propagated.

    Parameters
    ----------
        name : str
            The pipeline name associated with the work to be processed (e.g.
            dm-pipeline, fitburst, fluence)

        func : Callable[..., Tuple[Dict[str, Any], List[str], List[str]]]
            User function, returning (results, products, plots), called using
            parameters contained in the work object.

        lifetime : int
            Number of work items to process before exiting.
            Default is -1 (run indefinitely).

    """

    while lifetime != 0:
        work = Work.withdraw(pipeline=name)
        attempt_work(func, work)
        lifetime -= 1

    return


def attempt_work(user_func: FUNC_TYPE, work: Work):
    """
    Execute user func as a child process, terminating after work.timeout (s).
    Logs and propagates success/failure status.

    Parameters
    ----------
        user_func : Callable[..., Tuple[Dict[str, Any], List[str], List[str]]]
            Function returns (results, products, plots) tuple.  'results' is a
            generic dictionary, while 'products' and 'plots' are lists of paths.
            Executed as user_func(**work.parameters)

        work :
            chime_frb_api.workflow.Work object

    """

    def apply_func(connection, func, **kwargs):
        """Executes in child process & pipes results back"""
        connection.send(func(**kwargs))
        connection.close()

    receiver, sender = Pipe()  # used to pipe results back to parent

    process = Process(
        target=apply_func, args=(sender, user_func), kwargs=work.parameters
    )

    work.attempt += 1
    process.start()
    process.join(work.timeout if work.timeout > 0 else None)

    if process.is_alive():
        process.terminate()

    output = receiver.recv() if receiver.poll() else None

    if output and process.exitcode is 0:
        try:
            results, products, plots = output
            work.results = results
            work.products = products
            work.plots = plots
            work.status = "success"
        except:
            work.status = "failure"
    else:
        work.status = "failure"

    # Log possible outcomes
    if process.exitcode is 0 and work.status == "failure":
        logger.error("user func output doesn't match chime/frb standard")
    elif process.exitcode is None:
        logger.error("user func timed out")
    elif process.exitcode is not 0:
        logger.error("user func raised an error")
    else:
        logger.info("user func was successful")

    work.update()
    return
