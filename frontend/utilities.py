import uuid
import tomli
import base64, random, string
import nextcord


class SystemConfig:
    with open("../system_config.toml", mode="rb") as fp:
        system_config = tomli.load(fp) or None
    
