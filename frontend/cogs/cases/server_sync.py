import nextcord
import httpx
from nextcord.ext import commands
from utilities import requires_owner, system_config
from utility import logger
import os
import asyncio

class ServerSync(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="bans")
    async def bans(self, interaction: nextcord.Interaction):
        return
    
    @bans.subcommand(name="sync", description="Ban all scammers in our database from our server. This is required for API key moderations.")
    async def sync(self, interaction: nextcord.Interaction):
        await interaction.response.defer()

        try:
            async with httpx.AsyncClient() as client:
                case_dump_request = await client.post(
                    url=f"http://127.0.0.1:{system_config['api']['port']}/cases/dump",
                    json={
                        "master_password": system_config["api"]["master_password"]
                    }
                )
            case_dump_request = case_dump_request.json()
        except Exception as x:
            logger.error(x, debug=False)

        logger.warn(case_dump_request)

        try:
            names = []
            for case in case_dump_request.get("cases", {}):
                try:
                    accused_id = case.get("accused", 1234567890)

                    # Try to get the user, if it fails don't add to the queue
                    try:
                        user_obj = await self.bot.fetch_user(accused_id)

                        if not user_obj:
                            continue

                        bans = [ban async for ban in interaction.guild.bans()]
                        if any(ban.user.id == accused_id for ban in bans):
                            continue  # user is already banned

                        await interaction.guild.ban(user_obj, reason=f"[CROSSBAN] {case.get('_id', 'Unknown Case ID')}")
                        names.append(user_obj.global_name)
                        logger.ok(f"Banned {user_obj} from the server.", debug=True)

                        await asyncio.sleep(0.1)  # Sleep for 200ms to avoid hitting the rate limit
                        
                    except Exception as x:
                        logger.warn(f"Failed to fetch/ban user {accused_id} from the server. Skipping.", debug=True)
                        continue

                except Exception as x:
                    logger.error(x, debug=False)
                    return await interaction.followup.send("*Failed to digest the cases.", embed=nextcord.Embed(description=x), ephemeral=True)

            await interaction.followup.send(
                embed=nextcord.Embed(
                    title="Sync Result",
                    description=f"Ban List:\n```\n{chr(10).join(names)}\n```",
                    color=nextcord.Color.green()
                )
            )
            
        except:
            return await interaction.followup.send("*Failed to digest the cases.*", ephemeral=True)

def setup(bot):
    bot.add_cog(ServerSync(bot))
