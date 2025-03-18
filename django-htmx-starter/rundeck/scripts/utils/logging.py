import logging

def setup_logger(name, level="INFO"):
    """Configures logging for scripts, allowing dynamic log level selection."""
    numeric_level = getattr(logging, level.upper(), logging.INFO)  # Default to INFO if invalid
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    return logging.getLogger(name)
