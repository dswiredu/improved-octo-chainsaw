import time
from utils.logging import setup_logger  # Import centralized logger
from utils.argument_factory import get_default_parser  # Import default argparse parser

def main():
    parser = get_default_parser("Simulates a long-running task with progress updates.")
    parser.add_argument("--steps", type=int, default=5, help="Number of steps to simulate")
    parser.add_argument("--delay", type=float, default=5, help="Delay (in seconds) between steps")
    args = parser.parse_args()

    logger = setup_logger(__name__, args.log_level)

    logger.info("🚀 Starting long-running task...")
    for i in range(1, args.steps + 1):
        time.sleep(args.delay)
        logger.info(f"Step {i}/{args.steps} completed...")

    logger.info("✅ Long-running task finished!")

if __name__ == "__main__":
    main()
