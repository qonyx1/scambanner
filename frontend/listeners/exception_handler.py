import nextcord
from utility import logger
from nextcord.ext import commands

class ExceptionHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_application_command_error(self, interaction: nextcord.Interaction, error: str):
        logger.error(f"Command: {interaction.application_command.name or 'NaN'} | Author: {interaction.user.id or 'NaN'} | Error: {error or 'NaN'}")

def setup(bot):
    bot.add_cog(ExceptionHandler(bot))
