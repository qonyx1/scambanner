import nextcord
from utility import logger
from nextcord.ext import commands
from utilities import SystemConfig
system_config = SystemConfig.system_config

class GuildJoinHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild: nextcord.Guild):
        logger.ok(f"Joined a new guild: {guild.name} (ID: {guild.id})")
        
        embeds = [
            nextcord.Embed(
                title=f"👋 Welcome to the {system_config["discord"]["bot_name"]} Scam Network",
                description="Thank you for starting your journey with us! We hope that we can make your server more secure and deliver on all the promises we have made.",
                color=nextcord.Color.from_rgb(202, 17, 54)
            ).set_footer(text=f"Automated message sent from: {guild.name}"),
            nextcord.Embed(
                title="⚠️ Privacy Disclosure Policy",
                description=(
                    "By submitting proof, you acknowledge that you must disclose or link our privacy policy to the relevant parties. Additionally, you must make the proof provider aware that their proof will be uploaded publicly. Failure to do so will be considered a violation of our Privacy Policy."
                ),
                color=nextcord.Color.yellow()
            ).set_footer(text="If you do not comply with our privacy policy, it will result in a permanent bot blacklist."),
            nextcord.Embed(
                title="🛠️ Quick Startup",
                description="Go into your server and run `/set log_channel`. You're done! Nighthawk is now ready to ban scammers from your server and log them into your desired channel.",
                color=nextcord.Color.green()
            ).set_footer(text="If you encounter any problems, feel free to reach out to us.")
        ]

        try:
            await guild.owner.send(
                embeds=embeds
            )
        except:
            pass
        
def setup(bot):
    bot.add_cog(GuildJoinHandler(bot))
