"""Test lifecycle functions."""

import click

from workflow.definitions.work import Work
from workflow.examples.function import math
from workflow.lifecycle import configure, execute


def test_execute_function():
    """Test the execute function."""
    work = Work(pipeline="workflow-tests", site="local", user="tester")
    work.function = "workflow.examples.function.math"
    work.parameters = {"alpha": 5, "beta": 2}
    work = execute.function(work)
    results, products, plots = math(alpha=5, beta=2)
    assert work.results == results
    assert work.products == products
    assert work.plots == plots


def test_execute_function_with_click_cli():
    """Test the execute function with a click CLI."""
    work = Work(pipeline="workflow-tests", site="local", user="tester")
    work.function = "workflow.examples.function.cli"
    work.parameters = {"alpha": 1, "beta": 2}
    work = execute.function(work)
    results, products, plots = math(alpha=1, beta=2)
    assert work.results == results
    assert work.products == products
    assert work.plots == plots


def test_execute_function_with_click_cli_flags():
    """Test the execute function with a click CLI and parameters."""
    work = Work(pipeline="workflow-tests", site="local", user="tester")
    work.function = "workflow.examples.function.cli"
    work.parameters = {"alpha": 5, "beta": 2, "verbose": None}
    work = execute.function(work)
    results, products, plots = math(alpha=5, beta=2)
    assert work.results == results
    assert work.products == products
    assert work.plots == plots
    work.parameters = {"alpha": 5, "beta": 2}
    work = execute.function(work)
    assert work.results == results
    assert work.products != products
    assert work.plots != plots


def test_func_with_partials():
    """Test the function with partials."""
    work = Work(pipeline="workflow-tests", site="local", user="tester")
    work.function = "workflow.examples.function.math"
    work.parameters = {"alpha": 5}
    work = execute.function(work)
    results, products, plots = math(
        alpha=5,
    )
    assert work.results == results
    assert work.products == products
    assert work.plots == plots


def test_cli_with_partials():
    """Test the CLI with partials."""
    work = Work(pipeline="workflow-tests", site="local", user="tester")
    work.function = "workflow.examples.function.cli"
    work.parameters = {"alpha": 5}
    work = execute.function(work)
    results, products, plots = math(alpha=5, beta=2)
    assert work.results == results
    assert work.products == products
    assert work.plots == plots


def test_function_work_object():
    """Test the function with a work object."""
    work = Work(pipeline="workflow-tests", site="local", user="tester")
    work.function = "workflow.examples.function.worker"
    work.parameters = {"alpha": 5, "beta": 2}
    work = execute.function_with_work(work)
    results, products, plots = math(alpha=5, beta=2)
    assert work.results == results
    assert work.products == products
    assert work.plots == plots


def test_arguments_pass_false_and_zero_values():
    """False, 0 and "" are passed; only missing parameters use the defaults."""

    @click.command()
    @click.option("--trace/--no-trace", default=True)
    @click.option("--verbose", is_flag=True, default=False)
    @click.option("--retries", type=int, default=3)
    @click.option("--label", default="x")
    def cli(trace, verbose, retries, label):
        return {"trace": trace, "verbose": verbose, "retries": retries, "label": label}

    def args(parameters):
        work = Work(pipeline="workflow-tests", site="local", user="tester")
        work.parameters = parameters
        return configure.arguments(cli, work)

    assert args({"trace": False}) == ["--no-trace"]
    assert args({"trace": True}) == ["--trace"]
    assert args({"verbose": False}) == []
    assert args({"verbose": True}) == ["--verbose"]
    assert args({"retries": 0, "label": ""}) == ["--retries=0", "--label="]
    assert args({"trace": None, "retries": None}) == []

    work = Work(pipeline="workflow-tests", site="local", user="tester")
    work.parameters = {"trace": False, "retries": 0}
    # click parses them back to the values given
    outcome = cli.main(args=configure.arguments(cli, work), standalone_mode=False)
    assert outcome == {"trace": False, "verbose": False, "retries": 0, "label": "x"}

