import nextcord, requests
from data import Data

import json
from utilities import SystemConfig
system_config = SystemConfig.system_config
url = system_config["api"]["url"]
from utility import logger


from nextcord.ext import commands
from cogs.cases.case_delete_and_view import Cases

class CaseUtils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.guild_channel_cache = []

    @nextcord.slash_command(name="servers")
    async def servers(self, interaction):
        return
    
    @staticmethod
    async def main_log(self, embed: nextcord.Embed) -> bool:
        try:
            log_channel = int(system_config["discord"]["main_log_channel_id"])
            log_channel = await self.bot.fetch_channel(log_channel)
            await log_channel.send(embed=embed)
            return True
        except:
            return False

    

    @servers.subcommand(name="fetch", description="Check if a server is whitelisted.")
    async def fetch(self, interaction, guild_id: str):
        whitelist_entry = Data.database["bot"]["whitelists"].find_one({guild_id: {"$exists": True}})
        
        if whitelist_entry:
            channel_id = whitelist_entry[guild_id]
            await interaction.response.send_message(
                embed=nextcord.Embed(
                    title="Server Whitelisted",
                    description=f"The server with ID `{guild_id}` is whitelisted. Logging channel ID: `{channel_id}`.",
                    color=nextcord.Color.green()
                )
            )
            await self.main_log(self=self,
                embed=nextcord.Embed(
                    title="Server Whitelisted",
                    description=f"The server with ID `{guild_id}` is whitelisted. Logging channel ID: `{channel_id}`.",
                    color=nextcord.Color.green()
                )
            )
        else:
            await interaction.response.send_message(
                embed=nextcord.Embed(
                    title="Server Not Whitelisted",
                    description=f"The server with ID `{guild_id}` is not whitelisted.",
                    color=nextcord.Color.red()
                )
            )
            await self.main_log(self=self,
                embed=nextcord.Embed(
                    title="Server Not Whitelisted",
                    description=f"The server with ID `{guild_id}` is not whitelisted.",
                    color=nextcord.Color.red()
                )
            )


    @servers.subcommand(name="add", description="Add a whitelisted server that can create new cases.")
    async def add(self, interaction, guild_id: str, channel_id: str):
        
        try:
            guild = await self.bot.fetch_guild(guild_id)
            channel = await guild.fetch_channel(channel_id)
        except:
            await interaction.response.send_message(embed=nextcord.Embed(
                title="Invalid server/channel",
                description="I couldn't find this server. Please try again.",
                color=nextcord.Color.red()
            ))
            await self.main_log(embed=nextcord.Embed(self=self,
                title="Invalid server/channel",
                description="I couldn't find this server. Please try again.",
                color=nextcord.Color.red()
            ))
            return
        
        Data.database["bot"]["whitelists"].insert_one(
            {guild_id:channel_id}
        )

        await self.main_log(self=self,
            embed=nextcord.Embed(
                title="Server Whitelisted",
                description=f"{channel.jump_url} has been whitelisted, and the logging channel was set to {channel.mention}. Remember to use the format.",
                color=nextcord.Color.green()
            )
        )
        await interaction.response.send_message(
            embed=nextcord.Embed(
                title="Server Whitelisted",
                description=f"{channel.jump_url} has been whitelisted, and the logging channel was set to {channel.mention}. Remember to use the format.",
                color=nextcord.Color.green()
            )
        )


    @servers.subcommand(name="remove", description="Add a whitelisted server that can create new cases.")
    async def remove(
        self,
        interaction,
        guild_id: str
    ):
        
        try:
            guild = await self.bot.fetch_guild(guild_id)
        except:
            await self.main_log(self=self,embed=
nextcord.Embed(
    title="Invalid server",
    description="I couldn't find this server. Please try again.",
    color=nextcord.Color.red()
))
            await interaction.response.send_message(embed=nextcord.Embed(
                title="Invalid server",
                description="I couldn't find this server. Please try again.",
                color=nextcord.Color.red()
            ))
            return
        
        Data.database["bot"]["whitelists"].delete_one({guild_id: {"$exists": True}})

        n=nextcord.Embed(
            title="Server Removed",
            description=f"**{guild.name}** ({guild.id}) has been unwhitelisted, and I will no longer listen for new cases from this server.",
            color=nextcord.Color.green()
        )
        await interaction.response.send_message(
            embed=n
        )

        await self.main_log(
            self=self,
            embed=n
        )




            

def setup(bot):
    bot.add_cog(CaseUtils(bot))
