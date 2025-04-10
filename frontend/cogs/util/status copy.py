import nextcord
from nextcord.ext import commands
from utilities import requires_owner
import os

class Update(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="update", description="Update the bot to the latest version available.")
    @requires_owner() # very important !!!
    async def update(self, interaction: nextcord.Interaction, restart: bool):
        if restart:
            await interaction.response.send_message(
                embed=nextcord.Embed(
                    title="Bot Updating & Restarting",
                    description="The bot will automatically come online again. If it doesn't, the bot has errored.",
                    color=nextcord.Color.orange()
                )
            )
            os.system("bash ../update_and_run_bot_vers.sh")
        else:
            await interaction.response.send_message(
                embed=nextcord.Embed(
                    title="Updating Source Code",
                    description="Downloading and replacing the current bot tree, please wait.",
                    color=nextcord.Color.orange()
                )
            )
            os.system("bash ../update_bot_vers.sh")
            return


def setup(bot):
    bot.add_cog(Update(bot))