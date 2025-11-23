from utils.logger import configure_logger
from utils.io_capture import activate as _capture_io

configure_logger()  # console + rotating file logs
_capture_io()  # start logging every read_csv / read_excel path
