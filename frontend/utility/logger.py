import logging
from datetime import datetime
import os

COLORS = {
    "WARN": "\033[93m",
    "ERROR": "\033[91m",
    "OUTPUT": "\033[94m",
    "OK": "\033[92m",
    "RESET": "\033[0m"
}

logger = logging.getLogger("ColoredLogger")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()

class format(logging.Formatter):
    def format(self, record):
        date_str = datetime.now().strftime("%b%d %H:%M:%S")
        return f"{date_str.upper()} {record.getMessage()}"

handler.setFormatter(format())
logger.addHandler(handler)

def warn(msg):
    logger.warning(f"{COLORS['WARN']}[WARN]{COLORS['RESET']} {msg}")

def error(msg):
    logger.error(f"{COLORS['ERROR']}[ERROR]{COLORS['RESET']} {msg}")

def output(msg):
    logger.info(f"{COLORS['OUTPUT']}[OUTPUT]{COLORS['RESET']} {msg}")

def ok(msg):
    logger.info(f"{COLORS['OK']}[OK]{COLORS['RESET']} {msg}")
