from chime_frb_api.modules.buckets import Buckets
from somewhere import Results

def transfer_work(limit_per_run=1000):
    """Transfer successful Work from Buckets DB to Results DB
    """
    buckets = Buckets()
    results = Results()

    successful_work = buckets.view(
        query = {"status": "success"},
        projection = {},
        skip = 0, 
        limit = limit_per_run,
    )

    # do we need to deposit per pipeline? If so need to sort the successful work
    # by pipeline

    # rewrite this to make a list of successful work per pipeline instead of 
    # doing one deposit per item of work.
    pipelines = []
    for work in successful_work:
        pipelines.append(work.pipeline)

    pipelines = list(set(pipelines))

    for pipeline in pipelines:
        for work in successful_work:
            if work.pipeline == pipeline:
                status = results.deposit([work], pipeline=pipeline)
                if status ==True: # is this enough to confirm its deposited?
                    buckets.delete_ids([work.id])

    #somehow confirm that results were deposited?


if __name__ == "__main__":
    transfer_work()
    

