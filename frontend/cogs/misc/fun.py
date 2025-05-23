import nextcord
from nextcord.ext import commands
from utilities import requires_owner, blacklist_check  # Assuming this is where the decorator is defined.
from utilities import SystemConfig
system_config = SystemConfig.system_config

from main import local_version
from main import version

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    @nextcord.slash_command(name="troll", description="Sends a fake crossban message to a member")
    @requires_owner()
    @blacklist_check()
    async def troll(self, interaction, member: nextcord.Member) -> None:
        return
    

    @troll.subcommand(name="ban", description="Sends a fake crossban message to a member")
    @requires_owner()  # Ensure only the owner can use this command
    @blacklist_check()
    async def troll_ban(self, interaction, member: nextcord.Member) -> None:

        embed = nextcord.Embed(
            title=f"Automatic ban via the {system_config["discord"]["bot_name"]} Scam Network",
            description=f"You have been banned from one or more servers that participate in our crossban enforcement policy.\n\nDid we make a mistake? Too bad.",
            color=nextcord.Color.red()
        )
        embed.add_field(name="Case Reference Number", value="#694206f4")
        embed.set_footer(text="This is an automated massage. Contact our sales team if you think this was correct.")

        try:
            await member.send(embed=embed)
            return await interaction.response.send_message("*DMed this member successfully.*", ephemeral=True)
        except:
            return await interaction.response.send_message("*Failed to DM this member.*", ephemeral=True)


def setup(bot):
    bot.add_cog(Fun(bot))
