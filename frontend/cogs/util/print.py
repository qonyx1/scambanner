import nextcord
from nextcord.ext import commands
from utility import logger
from utilities import SystemConfig
system_config = SystemConfig.system_config

class Log(commands.Cog):
    def __init__(self, bot):
        self.bot = bot




    @nextcord.slash_command(name="log", description="Log something to the server.")
    async def log(self, interaction, message:str):
        print(message)
        await interaction.response.send_message("Logged to console!")

def setup(bot):
    bot.add_cog(Log(bot))