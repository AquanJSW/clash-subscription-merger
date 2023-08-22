import logging


def init_logger(name: str, level="WARNING", log_file=""):
    """Init a logger.

    Args
    ---
    level: str, optional - default: 'WARNING', the default level
    """
    logger = logging.getLogger(name)
    logger.propagate = False

    # If the logger has been initialized, return it.
    if logger.hasHandlers():
        logger.warning("Logger has been initialized, skip re-initialization.")
        return logger

    # Otherwise, initialize the logger.
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    handlers[-1].setFormatter(Formatter())
    handlers[-1].setLevel(level)
    if log_file:
        handlers.append(logging.FileHandler(log_file, mode="a", encoding="utf-8"))
        handlers[-1].setFormatter(Formatter())
        handlers[-1].setLevel("WARNING")
    logger.handlers = handlers
    logger.setLevel("DEBUG")
    return logger


class Formatter(logging.Formatter):
    """Custom logging formatter."""

    WHITE = "\x1b[37m"
    CYAN = "\x1b[36m"
    YELLOW = "\x1b[33m"
    RED = "\x1b[31m"
    BOLD_RED = "\x1b[31;1m"
    RESET = "\x1b[0m"

    # Example when having custom keys
    # FORMAT = "%(asctime)s %(name)s %(levelname)s %(localrank)s %(message)s"
    FORMAT = "%(asctime)s %(levelname)s %(message)s"

    # Full version:
    # %Y-%m-%d %H:%M:%S,uuu
    DATEFMT = "%m-%d %H:%M:%S"

    FORMATS = {
        logging.DEBUG: CYAN + FORMAT + RESET,
        logging.INFO: WHITE + FORMAT + RESET,
        logging.WARNING: YELLOW + FORMAT + RESET,
        logging.ERROR: RED + FORMAT + RESET,
        logging.CRITICAL: BOLD_RED + FORMAT + RESET,
    }

    def format(self, record):
        # Example when having custom keys
        # defaults = {'localrank': '\b'}
        defaults = {}

        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, self.DATEFMT, defaults=defaults)
        return formatter.format(record)


class IDAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        return '%s %s' % (self.extra['id'], msg), kwargs
