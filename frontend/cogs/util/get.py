import nextcord
from nextcord.ext import commands
from utility import logger
from utilities import requires_owner, blacklist_check, SystemConfig

system_config = SystemConfig.system_config

class Get(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="get", description="Get a variety of things.")
    @blacklist_check()
    async def get(self, interaction: nextcord.Interaction):
        return
    
    @get.subcommand(name = "user_from_id", description = "Gets a user from a Discord ID.")
    @blacklist_check()
    async def user_from_id(self, interaction: nextcord.Interaction, user: nextcord.User) -> None:
        try:
            await interaction.response.send_message(
                f"<@{user.id}>",
                allowed_mentions=nextcord.AllowedMentions(users=False)
            )
        except:
            await interaction.response.send_message(
                embed = nextcord.Embed(
                    title = "Oops!",
                    description = "I failed to find this user.",
                    color = nextcord.Color.red()
                )
            )

    @get.subcommand(name = "id_from_user", description = "Gets a ID from a user.")
    @blacklist_check()
    async def id_from_user(self, interaction: nextcord.Interaction, user: nextcord.User) -> None:
        try:
            await interaction.response.send_message(f"{user.id}")
        except:
            await interaction.response.send_message(
                embed = nextcord.Embed(
                    title = "Oops!",
                    description = "I failed to find this user or get their ID.",
                    color = nextcord.Color.red()
                )
            )

    @get.subcommand(name = "role_id", description = "Gets a ID from a role.")
    @blacklist_check()
    async def role_id(self, interaction: nextcord.Interaction, role: nextcord.Role) -> None:
        try:
            await interaction.response.send_message(f"{role.id}")
        except:
            await interaction.response.send_message(
                embed = nextcord.Embed(
                    title = "Oops!",
                    description = "I failed to find this user or get their ID.",
                    color = nextcord.Color.red()
                )
            )

    @get.subcommand(name = "server_id", description = "Gets a ID from a server.")
    @blacklist_check()
    async def server_id(self, interaction: nextcord.Interaction) -> None:
        try:
            await interaction.response.send_message(f"{interaction.guild.id}")
        except:
            await interaction.response.send_message(
                embed = nextcord.Embed(
                    title = "Oops!",
                    description = "I failed to find this user or get their ID.",
                    color = nextcord.Color.red()
                )
            )

def setup(bot):
    bot.add_cog(Get(bot))
