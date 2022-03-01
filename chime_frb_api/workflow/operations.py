"""Operations that can be performed on any work."""

import json
import logging
import os
from typing import List

from jwt import decode
from tenacity import retry, stop_after_attempt, stop_after_delay, wait_exponential

from chime_frb_api.core import API
from chime_frb_api.modules.bucket import Bucket
from chime_frb_api.tasks import Work

log = logging.getLogger(__name__)


class Tasks:
    """Tasks API"""

    def __init__(self, debug: bool = False, **kwargs):
        debug = True
        kwargs = {"base_url": "http://localhost:4357/buckets", "authentication": False}
        self.buckets = Bucket(debug=debug, **kwargs)

    @retry(
        stop=(stop_after_delay(30) | stop_after_attempt(3)),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def deposit(self, work: Work):
        """Deposit a work object into the bucket."""
        # Check if the user is defined
        if not work.user:
            token = self.buckets.access_token
            work.user = decode(token, options={"verify_signature": False}).get(
                "user_id", "unknown"
            )

        # If this is the first deposit, add work to the Tasks Database
        if not work.id:
            work.id = self.write(work)
        work.status = "queued"

        status = self.buckets.deposit(
            work=work.payload,
        )

        if status == False:
            work.status = "failure"
        self.modify(work) # modify is update in the Tasks DB, to be implemented

    def deposit_many(self, pipeline: str, works: List[Work]):
        """Deposit a list of work object into the bucket."""
        status = self.buckets.deposit_many([work.payload for work in work_list])
        if status == False:
            for work in works:
                work.status = "failure"
        for work in works:
            self.modify(work)

    def withdraw(self, pipeline: str) -> Work:
        """Withdraw work from the task queue corresponding to the pipeline.

        If work attributes `path`, `group`, and `config` are not set by the user
        then set from environment variables. Adds any tags from environment
        variables to `work.tags`. Sets `work.site`.

        Parameters
        ----------
        pipeline : str
            Name of the pipeline.

        Returns
        -------
        Work
            Work object for fetched work.
        """
        # Get work from bucket.
        payload = self.buckets.withdraw(
            pipeline=pipeline,
        )
        work = Work.from_dict(payload)

        # TODO: create a work.introspect() to do the
        # work object updates?

        # Check if path is default, if it is set to TASK_PATH
        if work.path == ".":
            work.path = os.environ.get("TASK_PATH", ".")

        # Add any TASK_TAGS to work.tags
        # TASK_TAGS is a list of strings encoded as a json string
        if "TASK_TAGS" in os.environ:
            task_tags = json.loads(os.environ["TASK_TAGS"])
            if work.tags:
                work.tags.extend(task_tags)
            else:
                work.tags = task_tags

            work.tags = list(set(work.tags))

        # If group not set by user, set from TASK_GROUP
        if not work.group:
            work.group = os.environ.get("TASK_GROUP")

        # If config not set by user, set from TASK_CONFIG
        if not work.config:
            work.config = os.environ.get("TASK_CONFIG")

        # Override site with TASK_SITE if env variable exists
        work.site = os.environ.get("TASK_SITE", work.site)

        # Set status to "running"
        work.status = "running"
        self.modify(work)

        return work

    def complete(self, work: Work):
        """[summary]

        Parameters
        ----------
        work : Work
            [description]
        """
        # anything else complete needs to do other than change status?
        # are we assuming the work is a success?? what if it fails?
        # do we need a fail(Work) method for people to use?
        work.status = "success" 
        self.buckets.update(work.payload)
        self.modify(work)

    ### Tasks DB operations
    def write(self, work: Work):
        pass

    def modify(self, work: Work):
        pass

    def remove(self, work: Work):
        pass

        
