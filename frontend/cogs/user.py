import nextcord, requests
from data import Data
from utility import logger
import json
from utilities import SystemConfig

system_config = SystemConfig.system_config
url = system_config["api"]["url"]

from nextcord.ext import commands

class Users(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="cases")
    async def cases(self, interaction):
        return
    

    # TODO: Make http://ip:port sync with settings
    @cases.subcommand(name="user", description="Evaluate if someone is registered in the database.")
    async def user(self, interaction, user: nextcord.User):
        logger.output(int(str(user.id).strip("<@!>")))
        request = requests.post(
            url = f"http://127.0.0.1:{system_config["api"]["port"]}/checks/check_id",
            json = {
                "accused_member": int(str(user.id).strip("<@!>"))
            }
        )

        logger.output(request)

        if request.status_code == 200:
            request = request.json()
            if request.get("code") == 0:
                await interaction.response.defer()

                case_request = requests.post(
                        url = f"http://127.0.0.1:{system_config["api"]["port"]}/cases/fetch_case",
                    json = {
                        "case_id": request.get("case_id")
                    }
                )

                if case_request.status_code == 200 and case_request.json().get("code") == 0:
                    case_request = (case_request.json()).get("case_data")

                    responsible_guild = await self.bot.fetch_guild(int(case_request.get("server_id"))) or "NaN"
                    accused = await self.bot.fetch_user(int(case_request.get("accused"))) or "NaN"
                    investigator = await self.bot.fetch_user(int(case_request.get("investigator"))) or "NaN"
                    
                    embed = nextcord.Embed(
                        title=f"📜 Case from {responsible_guild.name} ({responsible_guild.id})",
                        color=nextcord.Color.red()
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

                    embed.set_footer(text=f"🆔: {request.get('case_id')}")  

                    await interaction.edit_original_message(embed=embed)

                else:
                    await interaction.edit_original_message("*This member has an active case against them, but we couldn't find the details.*")
            else:
                await interaction.response.send_message("*This member has no active cases against them.*")
            
def setup(bot):
    bot.add_cog(Users(bot))
