import time

from utils.logging import setup_logger
from utils.argument_factory import get_default_parser

def main():
    parser = get_default_parser("Example script that prints a greeting message.")
    parser.add_argument("--name", type=str, help="Your name")
    parser.add_argument("--age", type=int, help="Your age")
    parser.add_argument("--verbose", action="store_true", help="Enable detailed output")
    args = parser.parse_args()

    logger = setup_logger(__name__, args.log_level)

    logger.info("✅ Example Script Started!")
    time.sleep(2)

    if args.name:
        logger.info(f"👋 Hello, {args.name}!")
    if args.age:
        logger.info(f"🎂 You are {args.age} years old.")

    if args.verbose:
        logger.debug("📝 Verbose mode enabled. Showing more details...")

    time.sleep(1)
    logger.info("✅ Example Script Completed!")

if __name__ == "__main__":
    main()
