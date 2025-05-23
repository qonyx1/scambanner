import nextcord, requests
from nextcord.ext import commands
from data import Data
from utility import logger
from utilities import SystemConfig

system_config = SystemConfig.system_config
url = system_config["api"]["url"]

class MemberJoin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: nextcord.Member):
        logger.ok(f"New member joined: {member.name} ({member.id}) in guild {member.guild.name} ({member.guild.id})", debug=True)
        
        request = requests.post(
            url=f"http://127.0.0.1:{system_config['api']['port']}/checks/check_id",
            json={"accused_member": member.id}
        )

        try:
            if guild.id == system_config["discord"]["main_guild_id"]:
                guild = member.guild
                banned_role_id = system_config["discord"]["banned_role_id"]
                banned_role = await guild.fetch_role(banned_role_id)
                
                if banned_role:
                    try:
                        await member.add_roles(banned_role, reason="Auto-assigned on join due to an active case")
                        logger.ok(f"Assigned banned role to {member.name}", debug=True)
                    except Exception as e:
                        logger.error(f"Failed to assign role to {member.name}: {e}", debug=False)
                else:
                    logger.warn(f"Banned role with ID {banned_role_id} not found in guild.", debug=False)
        except Exception as c:
            logger.error(c)
            pass
        
        if request.status_code == 200:
            request_data = request.json()
            if request_data.get("code") == 0:
                logger.ok(f"Member {member.id} has a case in the database: Case ID {request_data.get('case_id')}")
                
                case_request = requests.post(
                    url=f"http://127.0.0.1:{system_config['api']['port']}/cases/fetch_case",
                    json={"case_id": request_data.get("case_id")}
                )
                
                if case_request.status_code == 200 and case_request.json().get("code") == 0:
                    case_data = case_request.json().get("case_data")

                    try:
                        embed=nextcord.Embed(
                                title="You have been crossbanned",
                                description="You were found in our scammer database. View the reason for your case below."
                            )
                        embed.add_field(name="Case ID", value=request_data.get("case_id"))
                        embed.add_field(name="Reason", value=case_data["reason"])
                        await member.send(
                            embed=embed
                        )
                    except Exception as l:
                        logger.warn(l, debug=True)
                        pass
                    await member.ban(reason=f"[CROSSBAN] via caseid {request_data.get("case_id")}, created by investigator {str(case_data["investigator"])}")
                else:
                    logger.warn(f"Case details for {member.id} not found.", debug=True)
            else:
                logger.warn(f"Member {member.id} has no active cases.", debug=True)
        else:
            logger.error(f"Failed to check database for member {member.id}.", debug=True)

def setup(bot):
    bot.add_cog(MemberJoin(bot))
