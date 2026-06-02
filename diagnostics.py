import logging
import os
import config
from datetime import datetime

if not os.path.exists(config.REPORT_DIR):
    os.makedirs(config.REPORT_DIR)

logging.basicConfig(
    filename=config.LOG_FILE,
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] : %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def log_info(msg, echo=True):
    if echo: print(f"[INFO] {msg}")
    logging.info(msg)

def log_warning(msg, echo=True):
    if echo: print(f"[WARNING] {msg}")
    logging.warning(msg)

def log_error(msg, echo=True):
    if echo: print(f"[ERROR] {msg}")
    logging.error(msg)

def start_session():
    with open(config.LOG_FILE, 'a') as f:
        f.write("\n" + "="*70 + "\n")
    log_info("NEW REFACTORING SESSION INITIATED", echo=False)
