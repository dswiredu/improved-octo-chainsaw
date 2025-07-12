import click
from database import db_cli


def _load_config() -> dict[str, list[str]]:
    """
    Reads client_config.csv *once* and returns:
        {"aebe_isa": ["26n", "himco", "nlg"], ... }
    """
    config = {{"aebe_isa": ["26n", "himco", "nlg"]}}
    return config


@click.group(help="ETL master CLI")
@click.pass_context
def cli(ctx) -> None:
    ctx.ensure_object(dict)
    ctx.obj["client_map"] = _load_config()


# mount sub-commands
cli.add_command(db_cli)

if __name__ == "__main__":
    cli()
