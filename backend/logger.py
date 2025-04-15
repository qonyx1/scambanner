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
    print(f"{COLORS['WARN']}[WARN]{COLORS['RESET']} {msg.upper()}")

def error(msg, debug:bool=False):
    if not system_config["general"]["debug_mode"] and debug: return
    print(f"{COLORS['ERROR']}[ERROR]{COLORS['RESET']} {msg.upper()}")

def output(msg, debug:bool=False):
    if not system_config["general"]["debug_mode"] and debug: return
    print(f"{COLORS['OUTPUT']}[OUTPUT]{COLORS['RESET']} {msg.upper()}")

def ok(msg, debug:bool=False):
    if not system_config["general"]["debug_mode"] and debug: return
    print(f"{COLORS['OK']}[OK]{COLORS['RESET']} {msg.upper()}")
