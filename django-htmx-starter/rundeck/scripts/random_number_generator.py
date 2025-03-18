import time
import random
import click
from utils.logging import setup_logger
from utils.argument_factory import click_defaults  # Import Click argument defaults

@click.command()
@click_defaults()  # Automatically adds --log-level and --version
@click.option("--count", default=5, help="Number of random numbers to generate.")
@click.option("--min", default=1, help="Minimum value of random number.")
@click.option("--max", default=100, help="Maximum value of random number.")
def main(count, min, max, log_level, version):
    if version:
        click.echo("Random Number Generator - Version 1.0.0")
        return

    logger = setup_logger(__name__, log_level)
    logger.info(f"🎲 Generating {count} random numbers between {min} and {max}...")
    time.sleep(1)

    for i in range(count):
        logger.info(f"🔢 Random Number {i+1}: {random.randint(min, max)}")
        time.sleep(1)

    logger.info("✅ Random number generation complete!")

if __name__ == "__main__":
    main()
