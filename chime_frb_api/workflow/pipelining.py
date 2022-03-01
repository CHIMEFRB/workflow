"""Pipeline any method to be compatible with Tasks API."""

from functools import wraps

from .work import Work

def pipeline(name=None, lifetime=-1, retry=True):
    def _decorator(user_func):
        @wraps(user_func)  # propagates func name & doc-string
        def _wrapper(*args, **kwargs):
            try:
                work = Work.fetch(name)
                output = func(**work.parameters)
                results, products, plots = func(*args, **kwargs)
                work.results = results
                work.products = products
                work.plots = plots
                work.status = True
            except:
                work.status(False)
            finally:
                work.complete(str(work.Status))


        return _wrapper
    return _decorator

'''
global PRECURSORS
try:
    work = tasks.fetch(pipeline_name)
    results, products, plots = func(**work.parameters)
    work.status = True
    work.precursors = PRECURSORS
except:
    work.status = False
finally:
    task.complete(work)
    PRECURSORS = {}
'''
