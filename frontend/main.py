import nextcord
from nextcord.ext import commands
from dotenv import load_dotenv
import os
from utility import logger

load_dotenv()
client = commands.Bot(intents=nextcord.Intents.all())

def load_cogs():
    for folder in ["./cogs", "./listeners"]:
        for folder_path, _, files in os.walk(folder):
            if "__pycache__" in folder_path:
                continue
            for filename in files:
                if filename.endswith(".py"):
                    cog_path = folder_path.replace('./', '').replace(os.sep, '.')
                    logger.output(f'Loading cog: {filename}')
                    client.load_extension(f"{cog_path}.{filename[:-3]}")
                else:
                    logger.warn(f'Skipping file: {filename}')


@client.event
async def on_ready():
    print(f"\033[32m[OK]\033[0m Bot online, connected")

if __name__ == "__main__":
    load_cogs()
    client.run(os.getenv("TOKEN"))