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

class UnbanButton(Button):
    def __init__(self, guild_id: int, user_id: int):
        super().__init__(
            style=ButtonStyle.secondary,
            label="Unban from this server",
            custom_id=f"unban:{guild_id}:{user_id}",
        )

    async def callback(self, interaction: Interaction):
        if not interaction.user.guild_permissions.ban_members:
            await interaction.response.send_message(
                "*You do not have permission to unban members in this server.*",
                ephemeral=True
            )
            return
        
        return await interaction.response.send_message("*Due to security concerns, this command has been disabled until further notice. Feel free to [contribute here!](https://github.com/qonyx1/scambanner)*", ephemeral=True)

        # guild_id, user_id = map(int, self.custom_id.split(":")[1:])
        # try:
        #     guild = await interaction.client.fetch_guild(guild_id)
        #     user = await interaction.client.fetch_user(user_id)
        #     await guild.unban(user, reason=f"Manual unban by {interaction.user.id}")
        #     await interaction.response.send_message(
        #         f"*{user.name} has been unbanned from the server.*",
        #         ephemeral=True
        #     )
        # except Forbidden:
        #     await interaction.response.send_message("*I don’t have permission to unban in this server.*", ephemeral=True)
        # except Exception as e:
        #     await interaction.response.send_message(f"*Failed to unban this member. Are they banned?*", ephemeral=True)

class TemporaryUnbanView(View):
    def __init__(self):
        super().__init__(timeout=None)

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
                            view = None
                            if accused != "NaN" and responsible_guild != "NaN":
                                view = TemporaryUnbanView()
                                view.add_item(UnbanButton(guild_id=responsible_guild.id, user_id=accused.id))
                            await channel.send(embed=embed, view=view)
                        except Exception as d:
                            logger.error(f"[SEND_CASE_LOGS] Failed to send to {guild_id}/{channel_id}: {d}")
                            pass

                        await asyncio.sleep(0.2)
                    except Exception as e:
                        logger.error(f"[SEND_CASE_LOGS] Failed to send to {guild_id}/{channel_id}: {e}")

    except Exception as e:
        logger.error(f"[SEND_CASE_LOGS] {e}")
