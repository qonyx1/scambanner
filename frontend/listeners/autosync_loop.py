import httpx
from nextcord.ext import commands, tasks
from utility import logger
from utilities import SystemConfig, check_flag_status
import asyncio

system_config = SystemConfig.system_config
url = system_config["api"]["url"]

class AutoSync(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        logger.ok("Autosync Cog is ready.")
        if not self.sync_guilds.is_running():
            self.sync_guilds.start()

    @tasks.loop(minutes=30)
    async def sync_guilds(self):
        logger.warn("Syncing guilds...", debug=True)
        main_guild_id = system_config["discord"]["main_guild_id"]

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url=f"http://127.0.0.1:{system_config['api']['port']}/cases/dump",
                    json={"master_password": system_config["api"]["master_password"]}
                )
            case_dump_request = response.json()
        except Exception as e:
            logger.error(e, debug=False)
            return

        logger.warn(case_dump_request, debug=True)

        for guild in self.bot.guilds:
            if not await check_flag_status(guild.id, "auto_sync"):
                continue
            if guild.id != main_guild_id:
                try:
                    for case in case_dump_request.get("cases", {}):
                        accused_id = case.get("accused", 1234567890)
                        try:
                            user_obj = await self.bot.fetch_user(accused_id)
                            if not user_obj:
                                continue

                            bans = [ban async for ban in guild.bans()]
                            if any(ban.user.id == accused_id for ban in bans):
                                continue

                            await guild.ban(user_obj, reason=f"[CROSSBAN] {case.get('_id', 'Unknown Case ID')}")
                            logger.ok(f"Banned {user_obj} from the server.", debug=True)

                            await asyncio.sleep(1)
                        except Exception as e:
                            logger.warn(f"Failed to fetch/ban user {accused_id}. Skipping.", debug=True)
                            logger.error(e, debug=False)
                except Exception as e:
                    logger.error(e, debug=False)

    @sync_guilds.before_loop
    async def before_sync_guilds(self):
        await self.bot.wait_until_ready()

    @sync_guilds.error
    async def sync_guilds_error(self, error):
        logger.error(f"Error in sync_guilds task: {error}", debug=False)

def setup(bot):
    bot.add_cog(AutoSync(bot))
