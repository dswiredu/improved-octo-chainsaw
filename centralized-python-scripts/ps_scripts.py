import click
import subprocess


@click.group()
@click.pass_context
def ps_scripts(ctx: click.Context):
    """FE PS scripts"""
    pass

@ps_scripts.command()
@click.option("--arg1", type=str, help="Argument 1")
@click.option("--arg2", type=int, help="Argument 2")
def script1(arg1, arg2):
    """Run Script 3 (with argparse)"""
    # Call the argparse-based script via subprocess
    subprocess.run(
        ["python", "scripts/script3.py", "--arg1", arg1, "--arg2", str(arg2)]
    )


@ps_scripts.command()
@click.option("--arg1", type=str, help="Argument 1")
@click.option("--arg2", type=int, help="Argument 2")
def script2(arg1, arg2):
    """Run Script 3 (with argparse)"""
    # Call the argparse-based script via subprocess
    subprocess.run(
        ["python", "scripts/script3.py", "--arg1", arg1, "--arg2", str(arg2)]
    )
