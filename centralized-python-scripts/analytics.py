import click
import subprocess

@click.group()
@click.pass_context
def analytics(ctx: click.Context):
    """FE Analytics scripts"""
    pass


@click.command()
@click.option("--arg1", type=str, help="Argument 1")
@click.option("--arg2", type=int, help="Argument 2")
def command3(arg1, arg2):
    """Run Script 3 (with argparse)"""
    # Call the argparse-based script via subprocess
    subprocess.run(
        ["python", "scripts/script3.py", "--arg1", arg1, "--arg2", str(arg2)]
    )
