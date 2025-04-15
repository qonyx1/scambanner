import nextcord
from nextcord.ext import commands
from utilities import requires_owner
from utility import logger
import os
import asyncio

class Restart(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="restart", description="Restart the bot.")
    @requires_owner()
    async def restart(self, interaction: nextcord.Interaction):
        await interaction.response.send_message(
            embed = nextcord.Embed(
                title = "Bot Restarting",
                description="Please wait for the bot to restart.",
                color = nextcord.Color.orange()
            )
        )
        for statement in ["pm2 restart scambanner", "sudo pm2 restart scambanner"]:
            try:
                os.system(statement)
            except Exception as Error:
                logger.error(Error, debug=True)

        await self.bot.close()

def setup(bot):
    bot.add_cog(Restart(bot))
