# logging_utils.py

import logging

def setup_logging():
    logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s %(message)s')

def log_action(message):
    logging.info(message)
