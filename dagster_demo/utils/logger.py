import os
import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
OUTPUT_LOC = os.environ["ETL_LOC"]
LOCAL = os.getenv("LOCAL", False)


def get_log_path() -> str:
    """Creates the directory in which to store logs."""

    today = datetime.today().strftime("%Y-%m-%d")
    if os.getenv("LOCAL"):  # local testing
        logs_dir = "logs"
    else:
        logs_dir = os.path.join(OUTPUT_LOC, "logs")
    os.makedirs(logs_dir, exist_ok=True)

    log_filename = f"{today}.log"
    return os.path.join(logs_dir, log_filename)


def configure_logger() -> logging.Logger:
    """
    Creates a logging object that saves all logs to a file of the form
    <name_<today's date>.log
    """
    log_path = get_log_path()

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    if not root_logger.handlers:
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Console handler
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.INFO)
        stream_handler.setFormatter(formatter)

        # File handler
        # file_handler = logging.FileHandler(log_path)
        # file_handler.setLevel(logging.DEBUG)
        # file_handler.setFormatter(formatter)

        root_logger.addHandler(stream_handler)
        # root_logger.addHandler(file_handler)
    return root_logger
