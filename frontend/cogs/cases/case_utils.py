import nextcord, requests
from nextcord.ext import commands
from data import Data
from typeguard import typechecked
from utilities import SystemConfig, requires_owner
from utility import logger, webhook_logger

system_config = SystemConfig.system_config

class CaseUtils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="servers")
    async def servers(self, interaction):
        pass  # Placeholder for the main slash command

    @servers.subcommand(name="fetch", description="Check if a server is whitelisted.")
    @requires_owner()
    async def fetch(self, interaction, guild_id: str = None):
        if not guild_id:
            guild_id = str(interaction.guild.id)

        if not guild_id.isdigit():
            return await interaction.response.send_message("*Guild ID must be a number.*")

        try:
            whitelist_entry = Data.database["bot"]["whitelists"].find_one({guild_id: {"$exists": True}})
        except Exception as e:
            logger.error(f"[WHITELIST_FETCH] MongoDB error: {e}")
            return await interaction.response.send_message("*Error accessing the whitelist database.*")

        if whitelist_entry:
            entry = whitelist_entry[guild_id]
            channel_id = entry.get("channel_id")
            role_id = entry.get("role_id")

            await interaction.response.send_message(
                embed=nextcord.Embed(
                    title="✅ Server Whitelisted",
                    description=f"**Guild ID:** `{guild_id}`\n"
                                f"**Logging Channel:** `{channel_id}`\n"
                                f"**Role:** <@&{role_id}> (`{role_id}`)",
                    color=nextcord.Color.green()
                )
            )
        else:
            await interaction.response.send_message(
                embed=nextcord.Embed(
                    title="❌ Server Not Whitelisted",
                    description=f"No whitelist entry found for guild ID `{guild_id}`.",
                    color=nextcord.Color.red()
                )
            )

    @servers.subcommand(name="list", description="List all whitelisted servers and their logging channels.")
    @requires_owner()
    async def list_whitelisted(self, interaction):
        try:
            whitelist = Data.database["bot"]["whitelists"].find()
            entries = list(whitelist)
        except Exception as e:
            logger.error(f"[WHITELIST_LIST] MongoDB error: {e}")
            return await interaction.response.send_message("*Error retrieving whitelist entries.*")

        if not entries:
            return await interaction.response.send_message(
                embed=nextcord.Embed(
                    title="No Whitelisted Servers",
                    description="There are currently no whitelisted servers.",
                    color=nextcord.Color.red()
                )
            )

        embed = nextcord.Embed(
            title="Whitelisted Servers",
            color=nextcord.Color.blurple()
        )

        for entry in entries:
            entry.pop('_id', None)
            for guild_id, data in entry.items():
                try:
                    guild = await self.bot.fetch_guild(int(guild_id))
                    channel = await self.bot.fetch_channel(int(data.get("channel_id")))
                    embed.add_field(
                        name=f"{guild.name} ({guild.id})",
                        value=f"Channel: {channel.mention} (`{channel.id}`), Role: <@&{data.get('role_id')}>",
                        inline=False
                    )
                except Exception as e:
                    logger.warn(f"[WHITELIST_LIST] Could not fetch guild/channel: {e}")
                    embed.add_field(
                        name=f"Unknown Guild ({guild_id})",
                        value=f"Channel ID: `{data.get('channel_id')}` *(fetch failed)*",
                        inline=False
                    )

        await interaction.response.send_message(embed=embed)

    @servers.subcommand(name="add", description="Whitelist a server to create cases.")
    @requires_owner()
    async def add(self, interaction, guild_id: str, channel_id: str, role_id: str):
        if not all(id_.isdigit() for id_ in [guild_id, channel_id, role_id]):
            return await interaction.response.send_message("*All IDs must be numeric.*")

        try:
            guild = await self.bot.fetch_guild(int(guild_id))
            channel = await guild.fetch_channel(int(channel_id))
            role = guild.get_role(int(role_id))
            if role is None:
                raise ValueError("Role not found in guild")
        except Exception as e:
            logger.warn(f"[WHITELIST_ADD] Invalid data provided: {e}")
            return await interaction.response.send_message(
                embed=nextcord.Embed(
                    title="Invalid IDs",
                    description="One or more provided IDs are invalid or inaccessible.",
                    color=nextcord.Color.red()
                )
            )

        try:
            Data.database["bot"]["whitelists"].insert_one({
                guild_id: {"channel_id": channel_id, "role_id": role_id}
            })
        except Exception as e:
            logger.error(f"[WHITELIST_ADD] MongoDB error: {e}")
            return await interaction.response.send_message("*Error inserting into the whitelist.*")

        embed = nextcord.Embed(
            title="✅ Server Whitelisted",
            description=f"{channel.jump_url} is now a whitelisted logging channel.\n"
                        f"Role: <@&{role_id}>",
            color=nextcord.Color.green()
        )

        await webhook_logger.log_object(embed=embed)
        await interaction.response.send_message(embed=embed)

    @servers.subcommand(name="remove", description="Unwhitelist a server.")
    @requires_owner()
    async def remove(self, interaction, guild_id: str):
        if not guild_id.isdigit():
            return await interaction.response.send_message("*Guild ID must be a number.*")

        try:
            guild = await self.bot.fetch_guild(int(guild_id))
        except:
            return await interaction.response.send_message(
                embed=nextcord.Embed(
                    title="Invalid Server",
                    description="Guild not found or bot is not in it.",
                    color=nextcord.Color.red()
                )
            )

        result = Data.database["bot"]["whitelists"].delete_one({guild_id: {"$exists": True}})
        if result.deleted_count == 0:
            return await interaction.response.send_message(
                embed=nextcord.Embed(
                    title="Not Found",
                    description=f"No whitelist entry found for guild ID `{guild_id}`.",
                    color=nextcord.Color.red()
                )
            )

        embed = nextcord.Embed(
            title="✅ Server Removed",
            description=f"{guild.name} (`{guild.id}`) has been removed from the whitelist.",
            color=nextcord.Color.green()
        )

        await interaction.response.send_message(embed=embed)
        await webhook_logger.log_object(embed=embed)

def setup(bot):
    bot.add_cog(CaseUtils(bot))
