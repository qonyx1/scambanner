import nextcord
from nextcord.ext import commands

class Ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="ping", description="See if the bot's online. Obviously it is :rofl:")
    async def ping(self, interaction):
        await interaction.response.send_message("mrow x3 :D >:3")

def setup(bot):
    bot.add_cog(Ping(bot))