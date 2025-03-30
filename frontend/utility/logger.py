import logging
from datetime import datetime
import os
from utilities import SystemConfig
system_config = SystemConfig.system_config

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

def warn(msg, debug:bool=False):
    if not system_config["general"]["debug_mode"] and debug: return
    logger.warning(f"{COLORS['WARN']}[WARN]{COLORS['RESET']} {str(msg).upper()}")

def error(msg, debug:bool=False):
    if not system_config["general"]["debug_mode"] and debug: return
    logger.error(f"{COLORS['ERROR']}[ERROR]{COLORS['RESET']} {str(msg).upper()}")

def output(msg, debug:bool=False):
    if not system_config["general"]["debug_mode"] and debug: return
    logger.info(f"{COLORS['OUTPUT']}[OUTPUT]{COLORS['RESET']} {str(msg).upper()}")

def ok(msg, debug:bool=False):
    if not system_config["general"]["debug_mode"] and debug: return
    logger.info(f"{COLORS['OK']}[OK]{COLORS['RESET']} {str(msg).upper()}")
