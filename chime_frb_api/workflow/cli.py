"""Workflow command line interface."""

import click

from chime_frb_api.workflow.pipeline import run
from chime_frb_api.workflow.utils import prune_work


@click.group()
def cli():
    """Workflow Command Line Interface."""
    pass


cli.add_command(run)
cli.add_command(prune_work)

if __name__ == "__main__":
    cli()
