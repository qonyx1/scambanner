import nextcord
from nextcord.ext import commands
from utilities import requires_owner, SystemConfig, blacklist_check
from data import Data

db = Data.database
system_config = SystemConfig.system_config

class Logged(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="set")
    @blacklist_check()
    async def set(self, interaction: nextcord.Interaction):
        # This command serves as a parent for subcommands.
        await interaction.response.send_message("Use a subcommand with /set", ephemeral=True)
    
    @set.subcommand(
        name="log_channel",
        description="Set a channel that will receive notifications on new cases created by the bot"
    )
    # @requires_owner()
    @blacklist_check()
    async def log_channel(self, interaction: nextcord.Interaction, channel: nextcord.TextChannel):
        if channel.guild != interaction.guild:
            embed = nextcord.Embed(
                title="Invalid Channel",
                description="*You can only use a channel from this server.*",
                color=nextcord.Color.red()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        
        if interaction.user.id != interaction.guild.owner.id:
            embed = nextcord.Embed(
                title="Insufficient Permissions",
                description="*You do not own this server.*",
                color=nextcord.Color.red()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        
        try:
            record = db["log_channels"].find_one({"guild_id": str(interaction.guild.id)})
            if record:
                embed = nextcord.Embed(
                    title="Updating Log Channel",
                    description="A record already exists for this server. It will be updated.",
                    color=nextcord.Color.orange()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                embed = nextcord.Embed(
                    title="Creating Log Channel",
                    description="No record was found. Creating a new record.",
                    color=nextcord.Color.green()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = nextcord.Embed(
                title="Database Error",
                description="An error occurred while checking the database.",
                color=nextcord.Color.red()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        
        db["log_channels"].find_one_and_delete({"guild_id": str(interaction.guild.id)})
        
        db["log_channels"].insert_one({
            "guild_id": str(interaction.guild.id),
            "channel_id": str(channel.id)
        })
        
        try:
            if db["log_channels"].find_one({"guild_id": str(interaction.guild.id)}):
                embed = nextcord.Embed(
                    title="Success!",
                    description=f"The log channel has been set to {channel.mention}.",
                    color=nextcord.Color.green()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                embed = nextcord.Embed(
                    title="Insertion Failed",
                    description="The record could not be found in the database after insertion.",
                    color=nextcord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            embed = nextcord.Embed(
                title="Error",
                description="An error occurred while confirming the record in the database.",
                color=nextcord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        
def setup(bot):
    bot.add_cog(Logged(bot))
