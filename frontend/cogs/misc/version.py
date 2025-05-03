import nextcord
from nextcord.ext import commands
from utilities import requires_owner, blacklist_check  # Assuming this is where the decorator is defined.
from main import local_version
from main import version

class Version(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="version", description="Compare the local project version to the remote GitHub version.")
    @requires_owner()  # Ensure only the owner can use this command
    @blacklist_check()
    async def version(self, interaction) -> None:
        if local_version != version:
            col = nextcord.Color.red()
        else:
            col = nextcord.Color.green()

        await interaction.response.send_message(
            embed = nextcord.Embed(
                title = "Bot Version",
                description = "Compare the latest versions and determine if you need to run /update.",
                color = col
            ).add_field(name = "Local Version", value = local_version).add_field(name = "GitHub Version", value = version)
        )
        return

def setup(bot):
    bot.add_cog(Version(bot))
