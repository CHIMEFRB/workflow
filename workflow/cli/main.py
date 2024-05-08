"""Workflow command line interface."""

import click

# from workflow.cli.buckets import buckets
from workflow.cli.pipelines import pipelines
from workflow.cli.results import results
from workflow.cli.run import run
from workflow.cli.schedules import schedules
from workflow.cli.workspace import workspace


@click.group()
def cli():
    """Workflow Command Line Interface."""
    pass


cli.add_command(run)
# cli.add_command(buckets)
cli.add_command(results)
cli.add_command(pipelines)
cli.add_command(schedules)
cli.add_command(workspace)

if __name__ == "__main__":
    cli()
