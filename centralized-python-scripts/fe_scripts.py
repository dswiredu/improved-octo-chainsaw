import click
import commands


@click.group()
def cli():
    """Financial Engineers centralized Scripts CLI"""
    # add context here if needed
    pass


cli.add_command(commands.ps_scripts)
cli.add_command(commands.tools)
cli.add_command(commands.analytics)

if __name__ == "__main__":
    cli()
