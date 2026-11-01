"""Test the run command."""

from click.testing import CliRunner

from workflow.cli.run import run
from workflow.definitions.work import Work
from workflow.examples.function import math
from workflow.http.context import HTTPContext


def test_complete_work_run():
    """Test the complete work run."""
    work = Work(pipeline="complete", site="local", user="tester")
    work.function = "workflow.examples.function.math"
    work.parameters = {"alpha": 7, "beta": 11}
    work.event = [123]
    work.tags = ["test"]
    work.config.parent = "tester"
    results, _, _ = math(alpha=7, beta=11)
    work.deposit(return_ids=True)
    runner = CliRunner()
    result = runner.invoke(
        run,
        [
            "--site=local",
            "--lives=1",
            "--sleep=1",
            "--tag=test",
            "--event=123",
            "--parent=tester",
            "complete",
        ],
    )
    assert result.exit_code == 0
    ctx = HTTPContext(backends=["buckets"])
    response = ctx.buckets.view(
        query={"pipeline": "complete"}, projection={}, skip=0, limit=100
    )[0]
    assert response["pipeline"] == "complete"
    assert response["site"] == "local"
    assert response["user"] == "tester"
    assert response["function"] == "workflow.examples.function.math"
    assert response["parameters"] == {"alpha": 7, "beta": 11}
    assert response["results"] == results
    ctx.buckets.delete_many(pipeline="complete", force=True)


def test_run_without_a_terminal_writes_no_spinner(monkeypatch):
    """Without a terminal (e.g. a container's logs) no spinner frames are written."""
    import time
    from types import SimpleNamespace

    import workflow.cli.run as cli

    # nothing reaches the workspace file or the backends
    monkeypatch.setattr(cli.configure, "workspace", lambda workspace: None)
    monkeypatch.setattr(cli.read, "workspace", lambda path: {"sites": ["local"]})
    monkeypatch.setattr(cli.configure, "loki", lambda logger, config: False)
    buckets = SimpleNamespace(info=lambda: {"version": "test"})
    monkeypatch.setattr(
        cli, "HTTPContext", lambda backends: SimpleNamespace(buckets=buckets)
    )
    monkeypatch.setattr(cli, "lifecycle", lambda **kwargs: time.sleep(1.5))

    result = CliRunner().invoke(run, ["--site=local", "--lives=1", "complete"])

    assert result.exit_code == 0
    assert "Lifecycle" in result.output
    assert not any(0x2800 <= ord(char) <= 0x28FF for char in result.output)
