import nextcord, requests
from data import Data
import json
from utilities import SystemConfig
from typeguard import typechecked
system_config = SystemConfig.system_config
url = system_config["api"]["url"]

from utility import logger
from nextcord.ext import commands
from utilities import check_if_main_channel, requires_owner

class Cases(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="case")
    async def case(self, interaction):
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

    @case.subcommand(name="fetch", description="Fetch a case from the database.")
    async def user(self, interaction, case_id: str):

        await interaction.response.defer()

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
            
            embed = nextcord.Embed(
                title=f"📜 Case from {responsible_guild.name} ({responsible_guild.id})",
                color=nextcord.Color.green()
            )

            embed.add_field(
                name="🧑‍⚖️ Accused",
                value=f"{accused.name} ({accused.id})\n" if accused != "NaN" else "NaN",
                inline=False
            )

            embed.add_field(
                name="🔍 Investigator",
                value=f"{investigator.name} ({investigator.id})\n" if investigator != "NaN" else "NaN",
                inline=False
            )

            embed.add_field(
                name="⏳ Time",
                value=f"<t:{case_request.get('created_at', '0')}:F>\n",
                inline=False
            )

            embed.add_field(
                name="📌 Reason",
                value=f"```{case_request.get('reason') or 'NaN'}```\n",
                inline=False
            )

            proof_links = case_request.get("proof", [])
            if proof_links:
                embed.add_field(
                    name="🖼 Proof",
                    value="\n".join(proof_links),
                    inline=False
                )

            embed.set_footer(text=f"🆔: {case_id}")  

            await interaction.edit_original_message(embed=embed)

        else:
            logger.error(f"[CASE_FETCH] {case_request.json()} - {case_request.status_code}")
            await interaction.followup.send("*This case does not exist within our records.*")


    @case.subcommand(name="delete", description="Delete a case from the database.")
    @requires_owner()
    async def delete(self, interaction, case_id: str):
        await interaction.response.defer()

        case_request = requests.post(
            url = f"http://127.0.0.1:{system_config["api"]["port"]}/cases/fetch_case",
            json = {
                "case_id": case_id
            }
        )

        delete_request = requests.post(
            url = f"http://127.0.0.1:{system_config["api"]["port"]}/cases/delete_case",
            json = {
                "master_password": system_config["api"]["master_password"],
                "case_id": case_id
            }
        )

        # print(delete_request.json())

        if delete_request.status_code == 200 and (delete_request.json())["code"] == 0 and case_request.status_code == 200 and case_request.json().get("code") == 0:
            case_request = (case_request.json()).get("case_data")
            # print(case_request)

            embed = nextcord.Embed(
                title="Case Deleted",
                description="This case has been successfully deleted.",
                color=nextcord.Color.green()
            )


            responsible_guild = await self.bot.fetch_guild(int(case_request.get("server_id"))) or "NaN"
            accused = await self.bot.fetch_user(int(case_request.get("accused"))) or "NaN"
            investigator = await self.bot.fetch_user(int(case_request.get("investigator"))) or "NaN"
            
            embed.add_field(
                name="🧑‍⚖️ Accused",
                value=f"{accused.name} ({accused.id})\n" if accused != "NaN" else "NaN",
                inline=False
            )

            embed.add_field(
                name="🔍 Investigator",
                value=f"{investigator.name} ({investigator.id})\n" if investigator != "NaN" else "NaN",
                inline=False
            )

            embed.add_field(
                name="⏳ Time",
                value=f"<t:{case_request.get('created_at', '0')}:F>\n",
                inline=False
            )

            embed.add_field(
                name="📌 Reason",
                value=f"```{case_request.get('reason') or 'NaN'}```\n",
                inline=False
            )

            proof_links = case_request.get("proof", [])
            if proof_links:
                embed.add_field(
                    name="🖼 Proof",
                    value="\n".join(proof_links),
                    inline=False
                )

            embed.set_footer(text=f"🆔: {case_id}")  

            await interaction.edit_original_message(embed=embed)
            await self.main_log(self=self,embed=embed)

        else:
            await interaction.followup.send("*I couldn't fetch this case or delete it.*")




            
def setup(bot):
    bot.add_cog(Cases(bot))
