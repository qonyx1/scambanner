import nextcord
from nextcord.ext import commands
from utilities import requires_owner
import time
from data import Data

class BanSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="blacklist", description="Manage the blacklist of users.")
    @requires_owner()
    async def blacklist(self, interaction: nextcord.Interaction):
        return
    
    @blacklist.subcommand(name="add", description="Add a user to the blacklist.")
    @requires_owner()
    async def blacklist_add(self, interaction: nextcord.Interaction, user: nextcord.User):
        if Data.database.blacklists.find_one({"user_id": user.id}):
            await interaction.response.send_message(f"*User {user} is already blacklisted.*", ephemeral=True)
            return
        Data.database.blacklists.insert_one({"user_id": user.id})
        await interaction.response.send_message(f"*User {user} has been added to the blacklist.*", ephemeral=True)

    @blacklist.subcommand(name="remove", description="Remove a user from the blacklist.")
    @requires_owner()
    async def blacklist_remove(self, interaction: nextcord.Interaction, user: nextcord.User):
        if not Data.database.blacklists.find_one({"user_id": user.id}):
            await interaction.response.send_message(f"*User {user} is not blacklisted.*", ephemeral=True)
            return
        Data.database.blacklists.delete_one({"user_id": user.id})
        await interaction.response.send_message(f"*User {user} has been removed from the blacklist.*", ephemeral=True)



def setup(bot):
    bot.add_cog(BanSystem(bot))
