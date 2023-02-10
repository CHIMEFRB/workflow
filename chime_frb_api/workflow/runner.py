"""Workflow command line interface."""

import click

from chime_frb_api.workflow.cli.buckets import buckets
from chime_frb_api.workflow.cli.pipelines import pipelines
from chime_frb_api.workflow.cli.run import run


@click.group()
def cli():
    """Workflow Command Line Interface."""
    pass


cli.add_command(run)
cli.add_command(buckets)
cli.add_command(pipelines)

if __name__ == "__main__":
    cli()
