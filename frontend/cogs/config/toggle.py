import nextcord
from nextcord.ext import commands
from utilities import requires_owner, blacklist_check
from utility import logger
from data import Data
import os
import asyncio

class Toggle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @staticmethod
    async def update_fast_flag(interaction: nextcord.Interaction, status: bool) -> bool:
        try:
            Data.database["flags"].update_one(
                {"guild_id": interaction.guild.id, "flag_name": interaction.application_command.name},
                {"$set": {"status": status}},
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"[FLAGS] Failed to update fast flag: {e}")
            return False
        
    @staticmethod
    async def command_func(self, interaction: nextcord.Interaction, status: bool):
        if interaction.user.id != interaction.guild.owner.id:
            return await interaction.response.send_message("You are not the owner of this server.", ephemeral=True)
        
        if await self.update_fast_flag(interaction, status):
            return await interaction.response.send_message(f"{(interaction.application_command.name).title()} has been {'enabled' if status else 'disabled'}.", ephemeral=True)
        else:
            return await interaction.response.send_message(f"Failed to update the {interaction.application_command.name} status.", ephemeral=True)

    @nextcord.slash_command(name="toggle", description="Toggle a feature on or off")
    @blacklist_check()
    async def toggle(self, interaction: nextcord.Interaction):
        return
    
    @toggle.subcommand(name="auto_sync", description="Automatically reads bans from the database and syncs them to the guild.")
    @blacklist_check()
    async def auto_sync(self, interaction: nextcord.Interaction, status: bool):
        await self.command_func(interaction, status)
        
def setup(bot):
    bot.add_cog(Toggle(bot))
