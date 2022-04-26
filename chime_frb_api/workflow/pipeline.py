""" Fetch and process Work using any method compatible with Tasks API. """

import click
import logging
from time import sleep
from importlib import import_module
from multiprocessing import Process, Pipe
from typing import Callable, Tuple, Dict, Any, List

from chime_frb_api.workflow import Work


# Configure logger
LOGGING_FORMAT = "[%(asctime)s] %(levelname)s %(message)s"
logging.basicConfig(format=LOGGING_FORMAT, level=logging.INFO)
logger = logging.getLogger(__name__)


FUNC_TYPE = Callable[..., Tuple[Dict[str, Any], List[str], List[str]]]


@click.command()
@click.argument("bucket")
@click.argument("func")
@click.option(
    "--lifetime",
    default=-1,
    help="Work to do before exiting [default: -1 (forever)]",
)
def main(bucket, func, lifetime):
    """
    Fetches and attempts to process Work with user function,
    propagating success/failure status and results.

    BUCKET is the labelled priority queue work is withdrawn from.

    \b
    FUNC   is a pythonic module & function path (e.g. time.sleep),
           and is called with **work.parameters.

    """

    try:
        m, f = func.rsplit(".", 1)
        module = import_module(m)
        function = getattr(module, f)
    except ValueError:
        logger.error("Use 'package.module.function' formatting for FUNC.")
        return
    except ModuleNotFoundError:
        logger.error("Could not find module '%s'" % m)
        return
    except AttributeError:
        logger.error("Could not find function '%s' in module '%s'" % (f, m))
        return

    while lifetime != 0:
        _ = attempt_work(bucket, function)
        lifetime -= 1

    return


def attempt_work(name: str, user_func: FUNC_TYPE) -> Work:
    """
    Fetches 'work' object from appropriate bucket, then calls
    user_func(**work.parameters) in a child process, terminating after
    work.timeout (s). Sets results and success/failure status in work
    object, and then calls work.update().

    Parameters
    ----------
    name : str
        Specifies the bucket that the work object will be fetched from
        (e.g. dm-pipeline, fitburst, fitburst-some-dev-branch).

    user_func : Callable[..., Tuple[Dict[str, Any], List[str], List[str]]]
        Function returns (results, products, plots) tuple.  'results' is a
        generic dictionary, while 'products' and 'plots' are lists of paths.
        Executed as user_func(**work.parameters).

    Returns
    -------
    work.Work object
        The work object, populated with results and success/failure status.

    """

    def apply_func(connection, func, **kwargs):
        """Executes in child process & pipes results back"""
        connection.send(func(**kwargs))
        connection.close()

    receiver, sender = Pipe()  # to communicate with child

    work = Work.withdraw(pipeline=name)

    process = Process(
        target=apply_func, args=(sender, user_func), kwargs=work.parameters
    )

    work.attempt += 1
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
        except:
            work.status = "failure"
    else:
        work.status = "failure"

    # Log possible outcomes
    if process.exitcode == 0 and work.status == "failure":
        logger.error("user func output doesn't match chime/frb standard")
    elif process.exitcode == None:
        logger.error("user func timed out")
    elif process.exitcode != 0:
        logger.error("user func raised an error")
    else:
        logger.info("user func was successful")

    work.update()
    return work


if __name__ == "__main__":
    main()
