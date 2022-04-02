import logging
import os

PATH_TO_USERS_DATA_BASE = './data/users.json'
PATH_TO_PACKAGES_DATA_BASE = './data/barcodes.json'
RPT_LOGIN = os.environ.get('RPT_LOGIN', None)
RPT_PASSWORD = os.environ.get('RPT_PASSWORD', None)
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_API', None)
GLOBAL_LOGGER_LEVEL = os.environ.get('LOGGER_LEVEL', logging.INFO)

USERS_DATABASE = None
BARCODES_DATABASE = None
