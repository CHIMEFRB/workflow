from chime_frb_api.modules.buckets import Buckets
from somewhere import Results

def transfer_work(limit_per_run=1000):
    """Transfer successful Work from Buckets DB to Results DB
    """
    buckets = Buckets()
    results = Results()

    # do we need to deposit results per pipeline? Assuming so for now.
    pipelines = buckets.pipelines()

    for pipeline in pipelines:

        successful_work = buckets.view(
            query = {"status": "success", "pipeline": pipeline},
            projection = {}, # do we want everything?
            skip = 0, 
            limit = limit_per_run,
        )

        if len(successful_work):
            status = results.deposit(successful_work, pipeline=pipeline)
            if status ==True: # is this enough to confirm its deposited?
                buckets.delete_ids([work.id for work in successful_work])

if __name__ == "__main__":
    transfer_work()
    

