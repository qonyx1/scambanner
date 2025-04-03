import nextcord
from nextcord.ext import commands
from cogs.case_create import
class CaseLog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="ping", description="See if the bot's online. Obviously it is :rofl:")
    async def ping(self, interaction):
        await interaction.response.send_message("Alive")

def setup(bot):
    bot.add_cog(CaseLog(bot))
