import argparse
import click

def get_default_parser(description=""):
    """Returns an argparse parser with default arguments (log-level, version, etc.)."""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--log-level", type=str, default="INFO", help="Set logging level (DEBUG, INFO, WARNING, ERROR)")
    parser.add_argument("--version", action="version", version="1.0.0", help="Show script version and exit")
    return parser

def click_defaults():
    """
    Returns a decorator that adds default options (log-level, version, etc.) to Click commands.
    Usage: Apply to a Click function with `@click_defaults`
    """
    def decorator(func):
        func = click.option("--log-level", default="INFO", help="Set logging level (DEBUG, INFO, WARNING, ERROR)")(func)
        func = click.option("--version", is_flag=True, help="Show script version and exit")(func)
        return func

    return decorator
