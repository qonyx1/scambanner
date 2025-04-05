import nextcord
from nextcord.ext import commands
from utilities import requires_owner

class Ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="ping", description="See if the bot's online. Obviously it is :rofl:")
    @requires_owner()
    async def ping(self, interaction):
        await interaction.response.send_message("Alive")

def setup(bot):
    bot.add_cog(Ping(bot))