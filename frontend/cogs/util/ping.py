import nextcord
from nextcord.ext import commands
from utilities import blacklist_check
import time
from data import Data

class Ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="ping", description="Check bot, Discord API, and MongoDB latency.")
    @blacklist_check()
    async def ping(self, interaction: nextcord.Interaction):
        start_time = time.perf_counter()
        await interaction.response.defer()
        end_time = time.perf_counter()

        bot_latency = (end_time - start_time) * 100  # in ms
        api_latency = self.bot.latency * 1000         # websocket latency

        mongo_start = time.perf_counter()
        Data.database.command("ping")
        mongo_end = time.perf_counter()
        mongo_latency = (mongo_end - mongo_start) * 1000

        embed = nextcord.Embed(
            title="🏓 Pong!",
            description="View a representation of various statistics below. A lower number means better/faster!",
            color=nextcord.Color.green()
        )
        embed.add_field(name="Bot Latency", value=f"{bot_latency:.2f} ms", inline=True)
        embed.add_field(name="Discord API Latency", value=f"{api_latency:.2f} ms", inline=True)
        embed.add_field(name="MongoDB Latency", value=f"{mongo_latency:.2f} ms", inline=True)

        await interaction.followup.send(embed=embed)


def setup(bot):
    bot.add_cog(Ping(bot))
