import nextcord, requests
from data import Data
import json
from utilities import SystemConfig
system_config = SystemConfig.system_config
url = system_config["api"]["url"]

from nextcord.ext import commands

class Cases(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="case")
    async def case(self, interaction):
        return
    

<<<<<<< HEAD
    @case.subcommand(name="fetch", description="Fetch a case from the database.")
    async def user(self, interaction, case_id: str):
=======
    # TODO: Make http://ip:port sync with settings
    @case.subcommand(name="fetch", description="Fetch a case from the database.")
    async def user(self, interaction, caseid: str):
>>>>>>> fd55e2ff2029f4448b24ec2002c951a57164b1bd

        await interaction.response.defer()

        case_request = requests.post(
<<<<<<< HEAD
            url = f"http://127.0.0.1:{system_config["api"]["port"]}/cases/fetch_case",
            json = {
                
                "case_id": case_id
=======
            url = f"http://127.0.0.1:6565/cases/fetch_case",
            json = {
                
                "caseid": caseid
>>>>>>> fd55e2ff2029f4448b24ec2002c951a57164b1bd
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

<<<<<<< HEAD
            proof_links = case_request.get("proof", [])
            if proof_links:
                embed.add_field(
                    name="🖼 Proof",
                    value="\n".join(proof_links),
                    inline=False
                )

            embed.set_footer(text=f"🆔: {case_id}")  
=======
            evidence_links = case_request.get("proof", [])
            if evidence_links:
                embed.add_field(
                    name="🖼 Evidence",
                    value="\n".join(evidence_links),
                    inline=False
                )

            embed.set_footer(text=f"🆔: {caseid}")  
>>>>>>> fd55e2ff2029f4448b24ec2002c951a57164b1bd

            await interaction.edit_original_message(embed=embed)

        else:
<<<<<<< HEAD
            await interaction.followup.send("*This case does not exist within our records.*")
=======
            await interaction.edit_original_message("*This member has an active case against them, but we couldn't find the details.*")
>>>>>>> fd55e2ff2029f4448b24ec2002c951a57164b1bd











    @case.subcommand(name="delete", description="Delete a case from the database.")
<<<<<<< HEAD
    async def delete(self, interaction, case_id: str):
=======
    async def delete(self, interaction, caseid: str):
>>>>>>> fd55e2ff2029f4448b24ec2002c951a57164b1bd

        await interaction.response.defer()

        case_request = requests.post(
<<<<<<< HEAD
            url = f"http://127.0.0.1:{system_config["api"]["port"]}/cases/fetch_case",
            json = {
                "case_id": case_id
=======
            url = f"http://127.0.0.1:6565/cases/fetch_case",
            json = {
                "caseid": caseid
>>>>>>> fd55e2ff2029f4448b24ec2002c951a57164b1bd
            }
        )

        delete_request = requests.post(
<<<<<<< HEAD
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
=======
            url = f"http://127.0.0.1:6565/cases/delete_case",
            json = {
                "master_password": system_config["api"]["master_password"],
                "caseid": caseid
            }
        )

        if delete_request.status_code == 200 and (delete_request.json())["code"] == 0 and case_request.status_code == 200 and case_request.json().get("code") == 0:
            case_request = (case_request.json()).get("case_data")
>>>>>>> fd55e2ff2029f4448b24ec2002c951a57164b1bd

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

<<<<<<< HEAD
            proof_links = case_request.get("proof", [])
            if proof_links:
                embed.add_field(
                    name="🖼 Proof",
                    value="\n".join(proof_links),
                    inline=False
                )

            embed.set_footer(text=f"🆔: {case_id}")  
=======
            evidence_links = case_request.get("proof", [])
            if evidence_links:
                embed.add_field(
                    name="🖼 Evidence",
                    value="\n".join(evidence_links),
                    inline=False
                )

            embed.set_footer(text=f"🆔: {caseid}")  
>>>>>>> fd55e2ff2029f4448b24ec2002c951a57164b1bd

            await interaction.edit_original_message(embed=embed)

        else:
<<<<<<< HEAD
            await interaction.followup.send("*I couldn't fetch this case or delete it.*")
=======
            await interaction.edit_original_message("*This member has an active case against them, but we couldn't find the details.*")
>>>>>>> fd55e2ff2029f4448b24ec2002c951a57164b1bd




            
def setup(bot):
    bot.add_cog(Cases(bot))
