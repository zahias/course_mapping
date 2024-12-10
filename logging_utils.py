# logging_utils.py

import logging
import os

def setup_logging():
    log_file = 'app.log'
    logging.basicConfig(
        filename=log_file,
        filemode='a',
        format='%(asctime)s %(levelname)s:%(message)s',
        level=logging.INFO
    )
    logging.getLogger().addHandler(logging.StreamHandler())

def log_action(message):
    logging.info(message)
