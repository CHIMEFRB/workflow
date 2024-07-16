import time
from typing import Any, Dict, List

import pytest
from click.testing import CliRunner

from workflow.daemons import transfer
from workflow.definitions.work import Work
from workflow.http.context import HTTPContext


@pytest.fixture()
def works() -> List[Dict[str, Any]]:
    """Fixture for list of works.

    Returns:
        List[Dict[str, Any]]: list of works.
    """
    works: List[Dict[str, Any]] = []
    for i in range(5):
        work = Work(
            pipeline=f"sample-{i}",
            event=[i, i + 1],
            tags=[f"{i}"],
            site="local",
            user="tester",
        )
        work.config.archive.results = bool(i % 2)
        works.append(work.payload)
    return works


@pytest.fixture()
def ctx() -> HTTPContext:
    """Fixture for HTTPContext.

    Returns:
        HTTPContext: HTTPContext object.
    """
    ctx = HTTPContext()
    assert ctx.buckets.info()
    assert ctx.results.info()
    return ctx


@pytest.fixture()
def runner() -> CliRunner:
    """Fixture for CliRunner.

    Returns:
        CliRunner: CliRunner object.
    """
    return CliRunner()


def test_sucessful_work_delete(
    works: List[Dict[str, Any]], ctx: HTTPContext, runner: CliRunner
):
    """Tests workflow transfer daemon for successful work whose config.archive.results is False."""  # noqa
    for payload in works:
        work = Work.from_dict(payload)
        work.deposit(http=ctx)

    withdrawn = Work.withdraw(pipeline="sample-0", http=ctx)
    assert isinstance(withdrawn, Work)
    withdrawn.status = "success"
    withdrawn.config.archive.results = False
    withdrawn.update()

    result = runner.invoke(
        transfer.transfer,
        "--test-mode",
        standalone_mode=False,
    )
    assert result.exit_code == 0
    assert result.return_value == {"deleted": 1, "transfered": 0}


def test_sucessful_work_transfer(runner: CliRunner, ctx: HTTPContext):
    """Tests workflow transfer daemon for successful work whose config.archive.results is True."""  # noqa
    withdrawn = Work.withdraw(pipeline="sample-1", http=ctx)
    assert isinstance(withdrawn, Work)
    withdrawn.status = "success"
    withdrawn.config.archive.results = True
    withdrawn.update()

    results = runner.invoke(
        transfer.transfer,
        "--test-mode",  # noqa: E501
        standalone_mode=False,
    )
    assert results.exit_code == 0
    assert results.return_value == {"deleted": 1, "transfered": 1}


def test_failed_work_delete(ctx: HTTPContext, runner: CliRunner):
    """Tests transfer daemon for failed work whose config.archive.results is False."""
    withdrawn = Work.withdraw(pipeline="sample-2", http=ctx)
    assert isinstance(withdrawn, Work)
    withdrawn.status = "failure"
    withdrawn.attempt = withdrawn.retries
    withdrawn.update()

    results = runner.invoke(
        transfer.transfer,
        "--test-mode",
        standalone_mode=False,
    )
    assert results.exit_code == 0
    assert results.return_value == {"transfered": 0, "deleted": 1}


def test_failed_work_transfer(ctx: HTTPContext, runner: CliRunner):
    """Tests workflow transfer daemon for failed work whose config.archive.results is True."""  # noqa
    withdrawn = Work.withdraw(pipeline="sample-3", http=ctx)
    assert isinstance(withdrawn, Work)
    withdrawn.status = "failure"
    withdrawn.attempt = withdrawn.retries
    withdrawn.update()
    results = runner.invoke(
        transfer.transfer,
        "--test-mode",
        standalone_mode=False,
    )
    assert results.exit_code == 0
    assert results.return_value == {"transfered": 1, "deleted": 1}


def test_delete_stale_work(ctx: HTTPContext, runner: CliRunner):
    """Tests transfer daemon for stale work."""
    withdrawn = Work.withdraw(pipeline="sample-4", http=ctx)
    assert isinstance(withdrawn, Work)
    # Set creation time to be older than cutoff time (14 days)
    withdrawn.status = "failure"
    withdrawn.creation = time.time() - (60 * 60 * 24 * 14) - 1
    withdrawn.retries = 1
    withdrawn.attempt = 1
    withdrawn.update()
    results = runner.invoke(
        transfer.transfer,
        "--test-mode",
        standalone_mode=False,
    )
    assert results.exit_code == 0
    assert results.return_value == {"transfered": 0, "deleted": 1}


def test_cleanup_results(ctx: HTTPContext):
    """Tests workflow transfer daemon cleanup results."""
    for index in [1, 3]:
        pipeline = f"sample-{index}"
        result = ctx.results.view(
            pipeline=pipeline,
            query={},
            projection={"id": True},
        )
        assert ctx.results.delete_ids(pipeline, ids=[result[0]["id"]]) == {
            pipeline: True
        }
