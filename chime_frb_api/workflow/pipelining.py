""" Pipeline any method to be compatible with Tasks API. """

import logging
from time import sleep
from functools import wraps
from multiprocess import Process, Pipe

from .work import Work

# Configure logger
LOGGING_FORMAT = "[%(asctime)s] %(levelname)s %(message)s"
logging.basicConfig(format=LOGGING_FORMAT, level=logging.INFO)
logger = logging.getLogger(__name__)

def do_work(user_func, work):
    """ Execute user func, track timeouts & update work """
    
    def apply_func(connection, func, *args, **kwargs):
        """ Executes in child process & pipes results back """
        connection.send(func(**kwargs))
        connection.close()

    receiver, sender = Pipe()  # used to pipe results back to parent

    process = Process(
            target=apply_func,
            args=(sender, user_func),
            kwargs=work.parameters)

    process.start()
    process.join(work.timeout)

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
    else:
        logger.info("user func was successful")

    work.update()


def pipeline(name=None, lifetime=-1, retry=True):
    def _decorator(user_func):
        @wraps(user_func)  # propagates func name & doc-string
        def _wrapper(*args, **kwargs):
            
            if name is None:
                logger.info("Ignoring decorator (no pipeline name given)")
                return user_func(*args, **kwargs)

            completed = 0
            retrying = False

            while True:

                if retrying is False:
                    work = Work.withdraw(pipeline=name)

                do_work(user_func, work)
                
                retrying = work.status == "failure" and retry
                if retrying:
                    sleep(10)

                completed += 0 if retrying else 1
                if lifetime > 0 and completed >= lifetime:
                    break

        return _wrapper
    return _decorator
