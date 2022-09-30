""" Workflow command line interface """

import click

from chime_frb_api.workflow.pipeline import run


@click.group()
def cli():
    pass


cli.add_command(run)

if __name__ == "__main__":
    cli()
