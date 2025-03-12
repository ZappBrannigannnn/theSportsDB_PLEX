# logging_config.py
import os
import logging
from logging.handlers import RotatingFileHandler

# Set correct base directory
if os.name == 'nt':  # Windows
    base_dir = os.getenv('LOCALAPPDATA', os.path.expanduser("~"))

    # Define log file location
    log_file = os.path.join(
        base_dir,
        'Plex Media Server',
        'Logs',
        'SportsDBScanner.log'
    )

else:  # Linux/Debian 
    #base_dir = os.getenv('XDG_CONFIG_HOME', os.path.expanduser("~/.config")) ############################
    base_dir = "/var/lib/plexmediaserver/Library/Application Support/Plex Media Server/Logs"

    # Define log file location
    log_file = os.path.join(
        base_dir,
        'SportsDBScanner.log'
    )

# Ensure log directory exists
log_dir = os.path.dirname(log_file)
if not os.path.exists(log_dir):
    try:
        os.makedirs(log_dir)
    except OSError as e:
        if not os.path.isdir(log_dir):
            raise

# Configure logging
logger = logging.getLogger('SportsDBScanner')
logger.setLevel(logging.DEBUG)

# Prevent duplicate handlers
if not logger.handlers:
    handler = RotatingFileHandler(log_file, maxBytes=1024 * 1024, backupCount=5)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def LogMessage(message, level=logging.INFO):
    if level == logging.DEBUG:
        logger.debug(message)
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
