import nextcord, requests
from data import Data
from typeguard import typechecked
import json
from utilities import SystemConfig
system_config = SystemConfig.system_config
url = system_config["api"]["url"]
from utility import logger
from utilities import requires_owner

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
    @typechecked
    async def main_log(self, embed: nextcord.Embed) -> bool:
        try:
            log_channel = int(system_config["discord"]["main_log_channel_id"])
            log_channel = await self.bot.fetch_channel(log_channel)
            await log_channel.send(embed=embed)
            return True
        except:
            return False

    

    @servers.subcommand(name="fetch", description="Check if a server is whitelisted.")
    @requires_owner()
    async def fetch(self, interaction, guild_id: str = None):
        if guild_id is None:
            guild_id = str(interaction.guild.id)

        try:
            int(guild_id)
        except:
            return await interaction.response.send_message("*Guild ID must be a number.*")

        whitelist_entry = Data.database["bot"]["whitelists"].find_one({guild_id: {"$exists": True}})

        if whitelist_entry:
            entry = whitelist_entry[guild_id]
            channel_id = entry.get("channel_id")
            role_id = entry.get("role_id")

            await interaction.response.send_message(
                embed=nextcord.Embed(
                    title="Server Whitelisted",
                    description=f"The server with ID `{guild_id}` is whitelisted.\n"
                                f"Logging Channel ID: `{channel_id}`\n"
                                f"Role ID: `{role_id}` (<@&{role_id}>)",
                    color=nextcord.Color.green()
                )
            )
            await self.main_log(self=self,
                embed=nextcord.Embed(
                    title="Server Whitelisted",
                    description=f"The server with ID `{guild_id}` is whitelisted.\n"
                                f"Logging Channel ID: `{channel_id}`\n"
                                f"Role ID: `{role_id}`",
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

    @servers.subcommand(name="list", description="List all whitelisted servers and their logging channels.")
    @requires_owner()
    async def list_whitelisted(self, interaction):
        whitelist = Data.database["bot"]["whitelists"].find()
        entries = list(whitelist)

        if not entries:
            await interaction.response.send_message(
                embed=nextcord.Embed(
                    title="No Whitelisted Servers",
                    description="There are currently no whitelisted servers.",
                    color=nextcord.Color.red()
                )
            )
            return

        embed = nextcord.Embed(
            title="Whitelisted Servers",
            color=nextcord.Color.blurple()
        )

        for entry in entries:
            entry.pop('_id', None)  # Remove Mongo's ObjectId field
            for guild_id, channel_id in entry.items():
                try:
                    guild = await self.bot.fetch_guild(int(guild_id))
                    channel = await self.bot.fetch_channel(int(channel_id))
                    embed.add_field(
                        name=f"{guild.name} ({guild.id})",
                        value=f"Logging Channel: {channel.mention} (`{channel.id}`)",
                        inline=False
                    )
                except Exception as e:
                    embed.add_field(
                        name=f"Unknown Guild ({guild_id})",
                        value=f"Logging Channel ID: `{channel_id}` *(Could not fetch info)*",
                        inline=False
                    )

        await interaction.response.send_message(embed=embed)



    @servers.subcommand(name="add", description="Add a whitelisted server that can create new cases.")
    @requires_owner()
    async def add(self, interaction, guild_id: str, channel_id: str, role_id: str):
        try:
            int(guild_id)
            int(channel_id)
            int(role_id)
        except:
            return await interaction.response.send_message("*Guild/Channel/Role ID must be a number.*")

        try:
            guild = await self.bot.fetch_guild(guild_id)
            channel = await guild.fetch_channel(channel_id)
            role = guild.get_role(int(role_id))  # Role must be fetched from the guild
            if role is None:
                raise Exception("Role not found")
        except Exception as e:
            logger.warn(e, debug=True)
            await interaction.response.send_message(embed=nextcord.Embed(
                title="Invalid IDs",
                description="Could not find the specified server, channel, or role.",
                color=nextcord.Color.red()
            ))
            return

        Data.database["bot"]["whitelists"].insert_one(
            {guild_id: {"channel_id": channel_id, "role_id": role_id}}
        )

        await self.main_log(self=self,
            embed=nextcord.Embed(
                title="Server Whitelisted",
                description=f"{channel.jump_url} has been whitelisted. Log channel: {channel.mention}, Role: <@&{role_id}>.",
                color=nextcord.Color.green()
            )
        )
        await interaction.response.send_message(
            embed=nextcord.Embed(
                title="Server Whitelisted",
                description=f"{channel.jump_url} has been whitelisted. Log channel: {channel.mention}, Role: <@&{role_id}>.",
                color=nextcord.Color.green()
            )
        )


    @servers.subcommand(name="remove", description="Add a whitelisted server that can create new cases.")
    @requires_owner()
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
