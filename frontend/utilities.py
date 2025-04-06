import uuid, json, nextcord, asyncio
import tomli, requests
import base64, random, string
from typeguard import typechecked
from functools import wraps
from nextcord import Interaction, Member
from nextcord.ext.commands.errors import CheckFailure
from data import Data
from utility import logger
db = Data.database


class SystemConfig:
    with open("../system_config.toml", mode="rb") as fp:
        system_config = tomli.load(fp) or None

system_config = SystemConfig.system_config
url = system_config["api"]["url"]

def requires_owner() -> None:
    def decorator(func):
        @wraps(func)
        async def wrapper(self, interaction: Interaction, *args, **kwargs):
            member: Member = interaction.user
            if member.id in SystemConfig.system_config.get("discord", {}).get("additional_owners", []):
                return await func(self, interaction, *args, **kwargs)
            else:
                await interaction.response.send_message(
                    "*You do not have permission to use this command.*",
                    ephemeral=True
                )
                return
        return wrapper
    return decorator

def build_case_embed(responsible_guild: nextcord.Guild, accused: nextcord.User, investigator: nextcord.User, created_at: str, reason: str, proof_links: list):
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
            url = f"http://127.0.0.1:{system_config["api"]["port"]}/cases/fetch_case",
            json = {
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
                created_at=f"<t:{case_request.get("created_at", "0")}>",
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
                            await channel.send(embed=embed)
                        except Exception as d:
                            logger.error(f"[SEND_CASE_LOGS] Failed to send to {guild_id}/{channel_id}: {d}")
                            pass

                        await asyncio.sleep(0.2) # small delay
                    except Exception as e:
                        logger.error(f"[SEND_CASE_LOGS] Failed to send to {guild_id}/{channel_id}: {e}")

    except Exception as e:
        logger.error(f"[SEND_CASE_LOGS] {e}")
        

            
