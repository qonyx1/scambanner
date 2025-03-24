import nextcord
from nextcord.ext import commands

class Cases(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="case")
    async def cases(self, interaction):
        return
    
    @nextcord.command(name="case", description="Check if someone is registered in the database.")
    async def cases(self, interaction):
        await interaction.response.send_message("Alive")

def setup(bot):
    bot.add_cog(Cases(bot))