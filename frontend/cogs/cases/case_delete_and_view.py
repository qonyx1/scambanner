import nextcord
import requests
import json
import asyncio
from nextcord.ext import commands
from data import Data
from utilities import SystemConfig, check_if_main_channel, requires_owner
from utility import logger, webhook_logger
from typeguard import typechecked
from typing import Any, Optional, Callable

system_config = SystemConfig.system_config
url = system_config["api"]["url"]

MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds


async def safe_fetch(fetch_func: Callable[[int], Any], identifier: Any, id_type: str = "user") -> Any:
    try:
        return await fetch_func(int(identifier))
    except Exception as e:
        logger.warn(f"[FETCH_ERROR] Failed to fetch {id_type} ID {identifier}: {e}")
        return "NaN"


def safe_api_request(endpoint: str, payload: dict) -> Optional[dict]:
    full_url = f"http://127.0.0.1:{system_config['api']['port']}{endpoint}"
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(full_url, json=payload, timeout=5)
            if response.status_code == 200:
                return response.json()
            logger.warn(f"[API_ERROR] Non-200 response from {endpoint}: {response.status_code} | {response.text}")
        except requests.RequestException as e:
            logger.error(f"[API_ERROR] Attempt {attempt + 1} failed for {endpoint}: {e}")
        asyncio.run(asyncio.sleep(RETRY_DELAY))
    return None


class Cases(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="case")
    async def case(self, interaction: nextcord.Interaction):
        pass  # Placeholder command root

    @case.subcommand(name="fetch", description="Fetch a case from the database.")
    async def fetch(self, interaction: nextcord.Interaction, case_id: str):
        await interaction.response.defer()

        data = safe_api_request("/cases/fetch_case", {
            "master_password": system_config["api"]["master_password"],
            "case_id": case_id
        })

        if not data or data.get("code") != 0:
            return await interaction.followup.send("*This case does not exist within our records.*")

        case_data = data.get("case_data", {})

        responsible_guild = await safe_fetch(self.bot.fetch_guild, case_data.get("server_id"), "guild")
        accused = await safe_fetch(self.bot.fetch_user, case_data.get("accused"), "user")
        investigator = await safe_fetch(self.bot.fetch_user, case_data.get("investigator"), "user")

        embed = nextcord.Embed(
            title=f"📜 Case from {responsible_guild.name if responsible_guild != 'NaN' else 'Unknown Guild'}",
            color=nextcord.Color.green()
        )
        embed.add_field(name="🧑‍⚖️ Accused", value=f"{accused.name} ({accused.id})" if accused != "NaN" else "NaN", inline=False)
        embed.add_field(name="🔍 Investigator", value=f"{investigator.name} ({investigator.id})" if investigator != "NaN" else "NaN", inline=False)
        embed.add_field(name="⏳ Time", value=f"<t:{case_data.get('created_at', '0')}:F>", inline=False)
        embed.add_field(name="📌 Reason", value=f"```{case_data.get('reason') or 'NaN'}```", inline=False)

        if proof_links := case_data.get("proof"):
            embed.add_field(name="🖼 Proof", value="\n".join(proof_links), inline=False)

        embed.set_footer(text=f"🆔: {case_id}")
        await interaction.edit_original_message(embed=embed)

    @case.subcommand(name="delete", description="Delete a case from the database.")
    @requires_owner()
    async def delete(self, interaction: nextcord.Interaction, case_id: str):
        await interaction.response.defer()

        fetch_data = safe_api_request("/cases/fetch_case", {
            "master_password": system_config["api"]["master_password"],
            "case_id": case_id
        })

        if not fetch_data or fetch_data.get("code") != 0:
            return await interaction.followup.send("*This case does not exist or could not be retrieved.*")

        case_data = fetch_data.get("case_data", {})

        delete_data = safe_api_request("/cases/delete_case", {
            "master_password": system_config["api"]["master_password"],
            "case_id": case_id
        })

        if not delete_data or delete_data.get("code") != 0:
            return await interaction.followup.send("*Failed to delete this case. It may not exist or another error occurred.*")

        responsible_guild = await safe_fetch(self.bot.fetch_guild, case_data.get("server_id"), "guild")
        accused = await safe_fetch(self.bot.fetch_user, case_data.get("accused"), "user")
        investigator = await safe_fetch(self.bot.fetch_user, case_data.get("investigator"), "user")

        embed = nextcord.Embed(
            title=f"🗑 Case Deleted from {responsible_guild.name if responsible_guild != 'NaN' else 'Unknown Guild'}",
            color=nextcord.Color.red()
        )
        embed.add_field(name="🧑‍⚖️ Accused", value=f"{accused.name} ({accused.id})" if accused != "NaN" else "NaN", inline=False)
        embed.add_field(name="🔍 Investigator", value=f"{investigator.name} ({investigator.id})" if investigator != "NaN" else "NaN", inline=False)
        embed.add_field(name="⏳ Time", value=f"<t:{case_data.get('created_at', '0')}:F>", inline=False)
        embed.add_field(name="📌 Reason", value=f"```{case_data.get('reason') or 'NaN'}```", inline=False)

        if proof_links := case_data.get("proof"):
            embed.add_field(name="🖼 Proof", value="\n".join(proof_links), inline=False)

        embed.set_footer(text=f"🆔: {case_id} • Case deleted")
        await interaction.edit_original_message(embed=embed)

        msg = await interaction.followup.send(
            f"*Attempting to unban <@{accused.id}> from all servers..*",
            ephemeral=True
        )

        try:
            for guild in self.bot.guilds:
                try:
                    ban_entry = await guild.fetch_ban(accused)
                    if ban_entry.reason and ban_entry.reason.startswith("[CROSSBAN]"):
                        await guild.unban(user=accused, reason="[CROSSBAN] Case deleted by administrator, unbanned from all servers.")
                except Exception as e:
                    logger.error(f"[BAN_ERROR] Failed to check or unban {accused.id} from {guild.id}: {e}")

            await msg.edit(
                content=f"*Successfully unbanned <@{accused.id}> from all servers.*",
            )
        except Exception as l:
            await msg.edit(
                content=f"*Failed to unban <@{accused.id}> from all servers.*",
                embed=nextcord.Embed(
                    description=l
                )
            )
            return


def setup(bot):
    bot.add_cog(Cases(bot))
