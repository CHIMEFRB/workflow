"""Test lifecycle functions."""

from workflow.definitions.work import Work
from workflow.examples.function import math
from workflow.lifecycle import execute


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
    work = execute.function(work)
    results, products, plots = math(alpha=1, beta=2)
    assert work.results == results
    assert work.products == products
    assert work.plots == plots


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
