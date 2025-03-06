# logging_config.py
import os
import logging
from logging.handlers import RotatingFileHandler

log_file = os.path.join(
	os.getenv('LOCALAPPDATA'),  # AppData\Local on Windows
	'Plex Media Server',
	'Logs',
	'SportsDBScanner.log')
# Create the log file if it doesn't exist
if not os.path.exists(os.path.dirname(log_file)):
    os.makedirs(os.path.dirname(log_file))

# Set up the rotating file handler
# maxBytes: Maximum size of the log file before rotation (e.g., 1 MB)
# backupCount: Number of backup log files to keep
handler = RotatingFileHandler(log_file, maxBytes=1024 * 1024, backupCount=5)  # 1 MB per file, keep 5 backups

# Set the log format
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# Configure the root logger
logger = logging.getLogger('SportsDBScanner')
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

def LogMessage(message, level=logging.INFO):
    if level == logging.DEBUG:
        logger.debug(message)  # Use logger, not logging
    elif level == logging.INFO:
        logger.info(message)
    elif level == logging.WARNING:
        logger.warning(message)
    elif level == logging.ERROR:
        logger.error(message)
    elif level == logging.CRITICAL:
        logger.critical(message)
    else:
        logger.info(message)

