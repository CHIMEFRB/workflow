"""Workflow command line interface."""

from typing import List

import click
from rich.console import Console

from workflow.cli.buckets import buckets
from workflow.cli.configs import configs
from workflow.cli.pipelines import pipelines
from workflow.cli.results import results
from workflow.cli.run import run
from workflow.cli.schedules import schedules
from workflow.cli.workspace import workspace
from workflow.daemons.audit import audit
from workflow.daemons.transfer import transfer
from workflow.utils.read import get_active_workspace

console = Console()


class OrderedCommands(click.Group):
    """Order Click Commands."""

    def list_commands(self, ctx: click.Context) -> List[str]:
        """List Commands."""
        return list(self.commands)


@click.group(cls=OrderedCommands)
def cli():
    """Workflow Command Line Interface."""
    # ? Get Workspace
    message = get_active_workspace()
    console.print(message)
    pass


cli.add_command(run)
cli.add_command(buckets)
cli.add_command(results)
cli.add_command(configs)
cli.add_command(pipelines)
cli.add_command(schedules)
cli.add_command(workspace)
cli.add_command(audit)
cli.add_command(transfer)

if __name__ == "__main__":
    cli()
