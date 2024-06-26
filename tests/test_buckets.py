from typing import Any, Dict, List, Union

from workflow.definitions.work import Work
from workflow.http.context import HTTPContext

pipeline = "test-buckets"
http = HTTPContext(backends=["buckets"])


def test_buckets_lifecycle():
    """Test case where withdrawing from a pipeline with work deposited."""
    work = Work(pipeline=pipeline, user="tester", site="local")
    response: Union[bool, List[str]] = work.deposit(http=http)
    assert isinstance(response, bool)
    # Withdrawing from the bucket should return the work
    withdrawn: Work = Work.withdraw(pipeline=pipeline)
    assert withdrawn.status == "running"
    withdrawn.status = "success"
    # Update the work
    withdrawn.update()
    # Check that the work has been updated
    view = http.buckets.view(
        query={"pipeline": pipeline}, projection={"id": True, "status": True}
    )
    assert view[0]["status"] == "success"
    assert view[0]["id"] == withdrawn.id
    assert withdrawn.delete() is True


def test_withdraw_from_multiple_buckets():
    """Test case where withdrawing from multiple buckets."""
    pipelines = ["test-buckets-1", "test-buckets-2", "test-buckets-3"]
    works: List[Dict[str, Any]] = []
    for pipeline in pipelines:
        work = Work(pipeline=pipeline, user="tester", site="local")
        works.append(work.payload)
    # Deposit works using the buckets API Directly
    ids: Union[bool, List[str]] = http.buckets.deposit(works, return_ids=True)
    assert isinstance(ids, list)
    assert len(ids) == 3
    # Withdraw all works
    for _ in range(len(pipelines)):
        work: Work = Work.withdraw(pipeline=pipelines)  # type: ignore
        assert work.id in ids
    # Delete all works
    assert http.buckets.delete_ids(ids) is True


def test_delete_many():
    """Test case where deleting many works from a bucket."""
    pipeline = "delete-many-buckets"
    for _ in range(10):
        Work(
            pipeline=pipeline, user="tester", site="local", tags=["delete-many"]
        ).deposit()
    # Delete all works with the tag "delete-many"
    assert (
        http.buckets.delete_many(pipeline=pipeline, tags=["delete-many"], force=True)
        is True
    )
    # Check that the works have been deleted
    status = http.buckets.status(pipeline=pipeline)
    assert status["total"] == 0
