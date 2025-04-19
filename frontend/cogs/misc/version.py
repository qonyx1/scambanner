import nextcord
from nextcord.ext import commands
from utilities import requires_owner  # Assuming this is where the decorator is defined.
from main import local_version
from main import version

class Version(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="version")
    # @requires_owner()  # Ensure only the owner can use this command
    async def version(self, interaction):
        await interaction.response.send_message(
            embed = nextcord.Embed(
                title = "Version Comparison",
                color = nextcord.Color.orange() 
            ).add_field(name = "Local Version", value = local_version).add_field(name = "GitHub Version", value = version)
        )


def setup(bot):
    bot.add_cog(Version(bot))
