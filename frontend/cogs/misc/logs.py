import nextcord
from nextcord.ext import commands
from utilities import requires_owner, SystemConfig
from data import Data
db = Data.database
system_config = SystemConfig.system_config

class Logged(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="set")
    async def set(self, interaction):
        return
    
    @set.subcommand(name="log_channel", description="Set a channel that will receive notifications on new cases created by the bot")
    async def log_channel(self, interaction: nextcord.Interaction, channel: nextcord.TextChannel):
        if channel.guild != interaction.guild:
            return await interaction.response.send_message("*You can only use a channel in this server.*")
        
        # Removes duplicates
        db["log_channels"].find_one_and_delete(
            {str(interaction.guild.id): str(channel.id)}
        )


        db["log_channels"].insert_one(
            {str(interaction.guild.id): str(channel.id)}
        )
        
def setup(bot):
    bot.add_cog(Logged(bot))
