""" Fetch and process Work using any method compatible with Tasks API. """

import time
import click
import logging
from importlib import import_module
from multiprocessing import Process, Pipe
from typing import Optional, Callable, Tuple, Dict, Any, List

from chime_frb_api.workflow import Work

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
    help="Work to do before exiting [default: -1 (forever)]",
)
@click.option(
    "--sleep-time",
    type=int,
    default=10,
    help="Seconds to sleep between fetch attempts [default: 10]",
)
@click.option(
    "--base-url",
    type=str,
    default="http://frb-vsop.chime:8001",
    help="frb-master url [default: http://frb-vsop.chime:8001]",
)
@click.option(
    "--site",
    type=str,
    default="chime",
    help="site where work is being performed [default: chime]",
)
def run(pipeline, func, lifetime, sleep_time, base_url, site):
    """
    Withdraws Work object from appropriate bucket/pipeline,
    attempts to execute "func(**work.parameters)",
    then updates results and success/failure status.

    PIPELINE  bucket/pipeline Work is withdrawn from.

    FUNC      pythonic path for user func (package.module.function)


    """

    try:
        m, f = func.rsplit(".", 1)
        module = import_module(m)
        function = getattr(module, f)
    except:
        logger.error("Imports failed (use 'package.module.function' format)")
        return

    while lifetime != 0:
        work = attempt_work(pipeline, function, base_url, site)
        if work is None:
            sleep(sleep_time)
        else:
            lifetime -= 1

    return


def attempt_work(
    name: str, user_func: FUNC_TYPE, base_url: str, site: str
) -> Optional["Work"]:
    """
    Fetches 'work' object from appropriate pipeline/bucket, then calls
    user_func(**work.parameters) in a child process, terminating after
    work.timeout (s). Sets results and success/failure status in work
    object, and then calls work.update().

    Parameters
    ----------
    name : str
        Specifies the pipeline/bucket that work objects will be fetched from
        (e.g. dm-pipeline, fitburst, fitburst-some-dev-branch).

    user_func : Callable[..., Tuple[Dict[str, Any], List[str], List[str]]]
        Function returns (results, products, plots) tuple.  'results' is a
        generic dictionary, while 'products' and 'plots' are lists of paths.
        Executed as user_func(**work.parameters).

    base_url : str
        frb-master url (default http://frb-vsop.chime:8001)

    site : str
        site where work is processed (default chime). Options are chime,
        allenby, gbo, hatcreek, canfar, cedar, local.

    Returns
    -------
    work.Work object
        The work object, populated with results and success/failure status.

    """

    work = Work.withdraw(pipeline=name, site=site, base_url=base_url)
    if work is None:
        return

    def apply_func(connection, func, **kwargs):
        """Executes in child process & pipes results back"""
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
    run()
