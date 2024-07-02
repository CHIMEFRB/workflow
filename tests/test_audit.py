"""Test the audit daemon."""

import time
from typing import Any, Dict, List

import pytest
from click.testing import CliRunner

from workflow.daemons import audit
from workflow.definitions.work import Work
from workflow.http.context import HTTPContext


@pytest.fixture()
def works() -> List[Dict[str, Any]]:
    """Works fixture."""
    works = []
    for i in range(3):
        works.append(
            Work(
                pipeline=f"sample-{i}",
                event=[i, i + 1],
                tags=[f"{i}"],
                site="local",
                user="tester",
            ).payload
        )
    return works


def test_audit(works):
    """Tests workflow audit daemon."""
    runner = CliRunner()
    for payload in works:
        work = Work.from_dict(payload)
        work.deposit()

    auditor = runner.invoke(
        audit.audit,
        "--test-mode",
        standalone_mode=False,
    )
    assert auditor.exit_code == 0
    assert auditor.return_value == {"expired": 0, "failed": 0, "stale": 0}


def test_audit_failed():
    """Tests workflow audit daemon for failed work."""
    runner = CliRunner()
    withdrawn: Work = Work.withdraw(pipeline="sample-0")
    withdrawn.status = "failure"
    withdrawn.update()
    auditor = runner.invoke(
        audit.audit,
        "--test-mode",
        standalone_mode=False,
    )
    # sample-0 work is failed and requeued.
    assert auditor.exit_code == 0
    assert auditor.return_value == {"expired": 0, "failed": 1, "stale": 0}


def test_audit_expired():
    """Tests workflow audit daemon for expired work."""
    runner = CliRunner()
    withdrawn: Work = Work.withdraw(pipeline="sample-1")
    withdrawn.start = time.time() - 3600.0 * 2
    withdrawn.update()

    auditor = runner.invoke(
        audit.audit,
        "--test-mode",
        standalone_mode=False,
    )
    # sample-1 work is expired and marked as failure
    assert auditor.exit_code == 0
    assert auditor.return_value == {"expired": 1, "failed": 0, "stale": 0}


def test_audit_stale():
    """Tests workflow audit daemon for stale work."""
    runner = CliRunner()
    withdrawn: Work = Work.withdraw(pipeline="sample-2")
    withdrawn.creation = time.time() - 60 * 86400.0
    withdrawn.update()
    audit_results = runner.invoke(
        audit.audit,
        "--test-mode",
        standalone_mode=False,
    )
    # sample-2 work is stale;
    # the 1 failed work is the expired sample-1 work from previous test
    assert audit_results.exit_code == 0
    assert audit_results.return_value == {"expired": 0, "failed": 1, "stale": 1}


def test_delete_works():
    """Remove the work created for this test."""
    http = HTTPContext(backends=["buckets"])
    for i in range(3):
        status = http.buckets.delete_many(pipeline=f"sample-{i}", force=True)
        assert status is True
