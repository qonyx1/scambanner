import nextcord
from nextcord.ext import commands
from utilities import requires_owner, blacklist_check  # Assuming this is where the decorator is defined.

class KillBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="kill")
    @requires_owner()  # Ensure only the owner can use this command
    @blacklist_check()
    async def kill(self, interaction):
        await interaction.response.send_message("*Shutting down... Goodbye!*")
        await self.bot.close()  # Gracefully shuts down the bot.

def setup(bot):
    bot.add_cog(KillBot(bot))
