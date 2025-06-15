import logging
from os import makedirs, path

def setup_logger(logger_name, log_file, level=logging.DEBUG):
    logs_dir = 'logs'
    makedirs(logs_dir, exist_ok=True)

    logger = logging.getLogger(logger_name)
    logger.setLevel(level)

    # Prevent duplicate handlers if called multiple times
    if not logger.handlers:
        fh = logging.FileHandler(path.join(logs_dir, log_file))
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(module)s] - %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger
