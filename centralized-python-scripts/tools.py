import click
from tools.tool1 import awesome_tool

@click.group()
@click.pass_context
def tools(ctx: click.Context):
    """FE Tools"""
    pass

@tools.command()
# args....
def awesome_tool():
    awesome_tool(...)