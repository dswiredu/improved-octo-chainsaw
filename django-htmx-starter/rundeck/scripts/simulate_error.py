import time
import click
import sys
from utils.logging import setup_logger
from utils.argument_factory import click_defaults  # Import Click argument defaults

@click.command()
@click_defaults()  # Automatically adds --log-level and --version
@click.option("--steps", default=3, help="Number of steps before failure.")
@click.option("--delay", default=2, help="Delay (in seconds) between steps.")
def main(steps, delay, log_level, version):
    if version:
        click.echo("Simulate Error Script - Version 1.0.0")
        return

    logger = setup_logger(__name__, log_level)
    logger.info("⚠️ This script will fail after some steps.")
    
    for i in range(1, steps + 1):
        time.sleep(delay)
        logger.info(f"✅ Step {i} completed...")

    time.sleep(delay)
    logger.error("❌ ERROR: Simulated failure! Something went wrong.")
    sys.exit(1)  # Exit with an error code

if __name__ == "__main__":
    main()
