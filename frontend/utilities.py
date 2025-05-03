import uuid, json, nextcord, asyncio
import tomli, requests
import base64, random, string
from typeguard import typechecked
from functools import wraps
from nextcord import Interaction, Member, Forbidden, ButtonStyle
from nextcord.ui import Button, View
from data import Data
from utility import logger

class SystemConfig:
    with open("../system_config.toml", mode="rb") as fp:
        system_config = tomli.load(fp) or None

db = Data.database
system_config = SystemConfig.system_config
url = system_config["api"]["url"]


@typechecked
async def check_if_channel_whitelist(self, interaction: nextcord.Interaction) -> bool:

    whitelist_entry = db["bot"]["whitelists"].find_one({str(interaction.guild.id): {"$exists": True}})
    if whitelist_entry:
        channel_id = whitelist_entry.get(str(interaction.guild.id))
        if channel_id == interaction.channel.id:
            return True
        else: return False
    else: return False

@typechecked
async def check_if_main_channel(self, interaction: nextcord.Interaction) -> bool:
    main_channel_id = system_config["discord"]["main_channel_id"] or 0

    if interaction.channel.id != main_channel_id:
        return True
    else: return False

@typechecked
@staticmethod
async def check_flag_status(guild_id: int, flag_name: str) -> bool:
    flag = db["flags"].find_one({"guild_id": guild_id, "flag_name": flag_name})
    
    if flag:
        return flag.get("status", False)
    else:
        return False
    return False

def requires_owner() -> None:
    def decorator(func):
        @wraps(func)
        async def wrapper(self, interaction: Interaction, *args, **kwargs):
            member: Member = interaction.user
            if member.id in SystemConfig.system_config.get("discord", {}).get("additional_owners", []):
                await func(self, interaction, *args, **kwargs)
                return
            else:
                await interaction.response.send_message(
                    "*You do not have permission to use this command.*",
                    ephemeral=True
                )
                return
        return wrapper
    return decorator

def blacklist_check():
    def decorator(func):
        @wraps(func)
        async def wrapper(self, interaction: Interaction, *args, **kwargs):
            blacklist_entry = Data.database.blacklists.find_one({"user_id": interaction.user.id})

            if blacklist_entry is not None:
                embed = nextcord.Embed(
                    title="Blacklisted",
                    description="You have been blacklisted from interacting with this bot."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            return await func(self, interaction, *args, **kwargs)

        return wrapper
    return decorator

@typechecked
def build_case_embed(responsible_guild: nextcord.Guild, accused: nextcord.User, investigator: nextcord.User, created_at: str, reason: str, proof_links: list) -> nextcord.Embed:
    embed = nextcord.Embed(
        title=f"📜 Case from {responsible_guild.name} ({responsible_guild.id})",
        color=nextcord.Color.red()
    )
    embed.add_field(
        name="🧑‍⚖️ Accused",
        value=f"{accused.name} ({accused.id})" if accused != "NaN" else "NaN",
        inline=False
    )
    embed.add_field(
        name="🔍 Investigator",
        value=f"{investigator.name} ({investigator.id})",
        inline=False
    )
    embed.add_field(
        name="⏳ Time",
        value=created_at,
        inline=False
    )
    embed.add_field(
        name="📌 Reason",
        value=reason,
        inline=False
    )
    if proof_links:
        embed.add_field(
            name="🖼 Proof",
            value="\n".join(proof_links),
            inline=False
        )
    return embed

async def send_case_logs(self, case_id: str) -> bool:
    try:
        case_request = requests.post(
            url=f"http://127.0.0.1:{system_config['api']['port']}/cases/fetch_case",
            json={
                "master_password": system_config["api"]["master_password"],
                "case_id": case_id
            }
        )

        if case_request.status_code == 200 and case_request.json().get("code") == 0:
            case_request = (case_request.json()).get("case_data")

            responsible_guild = await self.bot.fetch_guild(int(case_request.get("server_id"))) or "NaN"
            accused = await self.bot.fetch_user(int(case_request.get("accused"))) or "NaN"
            investigator = await self.bot.fetch_user(int(case_request.get("investigator"))) or "NaN"

            embed = build_case_embed(
                responsible_guild=responsible_guild,
                accused=accused,
                investigator=investigator,
                created_at=f"<t:{case_request.get('created_at', '0')}>",
                reason=case_request.get("reason", "NaN"),
                proof_links=case_request.get("proof", [])
            )

            log_channels = db["log_channels"].find()

            for entry in log_channels:
                guild_id = entry.get("guild_id")
                channel_id = entry.get("channel_id")

                if guild_id and channel_id:
                    try:
                        guild = await self.bot.fetch_guild(int(guild_id))
                        channel = await guild.fetch_channel(int(channel_id))
                        try:
                            message = await channel.send(embed=embed)

                            # Create a thread for proof links
                            if case_request.get("proof"):
                                try:
                                    thread = await message.create_thread(
                                        name="Proof Quickview",
                                        auto_archive_duration=1440  # 24 hours
                                    )
                                    proof_links = case_request.get("proof", [])
                                    await thread.send("\n".join(proof_links))
                                except Exception as thread_error:
                                    logger.error(f"[SEND_CASE_LOGS] Failed to create thread in {guild_id}/{channel_id}: {thread_error}")
                                    pass

                        except Exception as d:
                            logger.error(f"[SEND_CASE_LOGS] Failed to send to {guild_id}/{channel_id}: {d}")
                            pass

                        await asyncio.sleep(0.2)
                    except Exception as e:
                        logger.error(f"[SEND_CASE_LOGS] Failed to send to {guild_id}/{channel_id}: {e}")
    except Exception as e:
        logger.error(f"[SEND_CASE_LOGS] {e}")

