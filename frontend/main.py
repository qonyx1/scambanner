import nextcord
from nextcord.ext import commands
from dotenv import load_dotenv
import os, requests
import logging
from utility import logger
from utilities import SystemConfig
system_config = SystemConfig.system_config
load_dotenv()
client = commands.Bot(intents=nextcord.Intents.all()) # dont worry it works



url = "https://raw.githubusercontent.com/qonyx1/scambanner/refs/heads/main/.VERSION"

with open("../.VERSION", "r") as f:
    local_version = f.read()

try:
  version = requests.get(url=url).text

  if version != local_version:
    logger.warn("THIS INSTANCE IS OUTDATED. PLEASE VISIT THE MAIN REPOSITORY AND UPDATE YOUR SOFTWARE VERSION IMMEDIATELY")
except Exception as e:
  logger.error(f"Error fetching version: {e}")
  version = "NaN"

text = rf"""

                          _                                 
                         | |                                
  ___  ___ __ _ _ __ ___ | |__   __ _ _ __  _ __   ___ _ __ 
 / __|/ __/ _` | '_ ` _ \| '_ \ / _` | '_ \| '_ \ / _ \ '__|
 \__ \ (_| (_| | | | | | | |_) | (_| | | | | | | |  __/ |   
 |___/\___\__,_|_| |_| |_|_.__/ \__,_|_| |_|_| |_|\___|_|   
                                                            
     Beginning execution | v{local_version} | github.com/qonyx1

     

"""

from pystyle import Center
print(Center.XCenter(text))

def load_cogs():
    for folder in ["./cogs", "./listeners"]:
        for folder_path, _, files in os.walk(folder):
            if "__pycache__" in folder_path:
                continue
            for filename in files:
                if filename.endswith(".py"):
                    cog_path = folder_path.replace('./', '').replace(os.sep, '.')
                    logger.warn(f'Loading cog: {filename}')
                    client.load_extension(f"{cog_path}.{filename[:-3]}")
                else:
                    logger.error(f'Skipping file: {filename}')


@client.event
async def on_ready():
    logger.ok(f"Discord bot has been started")

if __name__ == "__main__":
    load_cogs()

    if system_config["general"]["debug_mode"] != True:
        logging.getLogger("fastapi").setLevel(logging.CRITICAL + 9) # remove all fastapi logging, set to ERROR if wanted
        logging.getLogger("nextcord").setLevel(logging.CRITICAL + 9) # remove all nextcord logging, set to ERROR if wanted

    client.run(os.getenv("TOKEN"))
