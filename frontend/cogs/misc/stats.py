import nextcord
from nextcord.ext import commands
from utility import logger
from utilities import SystemConfig, blacklist_check
system_config = SystemConfig.system_config
from data import Data
database = Data.database

import requests
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
from io import BytesIO
from datetime import datetime, timedelta

class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="stats", description="Commands related to stats")
    @blacklist_check()
    async def stats(self, interaction: nextcord.Interaction):
        pass

    @stats.subcommand(name="user", description="View the activity of a user.")
    @blacklist_check()
    async def user(self, interaction: nextcord.Interaction, member: nextcord.Member, timeframe: str = nextcord.SlashOption(choices={"14 Days": "14d", "7 Days": "7d", "30 Days": "30d"})):
        await interaction.response.defer()

        try:
            response = requests.post(
                url=f"http://127.0.0.1:{system_config['api']['port']}/cases/dump",
                json={"master_password": system_config['api']['master_password']}
            )
            data = response.json()
        except Exception as e:
            await interaction.followup.send("Error fetching cases from the API.")
            logger.error(f"API request error: {e}")
            return

        cases = data.get("cases", [])
        user_id = member.id
        now = datetime.now()
        days_ago = now - timedelta(days=int(timeframe[:-1]))

        counts = { (days_ago + timedelta(days=i)).date(): 0 for i in range(int(timeframe[:-1]) + 1) }

        for case in cases:
            try:
                inv_id = int(case.get("investigator", "0"))
            except ValueError:
                logger.warning(f"Could not convert investigator field to int: {case.get('investigator')}")
                continue

            if inv_id != user_id:
                continue

            try:
                created_at = datetime.fromtimestamp(case.get("created_at", 0))
            except Exception as e:
                logger.warning(f"Error converting timestamp: {case.get('created_at')}, error: {e}")
                continue

            if days_ago <= created_at <= now:
                created_date = created_at.date()
                if created_date in counts:
                    counts[created_date] += 1

        days = sorted(counts.keys())
        counts_list = [counts[day] for day in days]

        plt.style.use("seaborn-v0_8-darkgrid")
        fig, ax = plt.subplots(figsize=(10, 5))
        fig.patch.set_facecolor("#0f0f0f")

        bars = ax.bar(days, counts_list, color="#5dade2", width=0.6, edgecolor="#5dade2", linewidth=1.5)
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'{int(height)}', xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 6), textcoords="offset points", ha="center", va="bottom",
                        fontsize=10, color="#ffffff")

        ax.set_xlabel("Date", fontsize=12, color="#ffffff")
        ax.set_ylabel("# Cases", fontsize=12, color="#ffffff")
        ax.set_title(f"Cases in the Past {int(timeframe[:-1])} Days", fontsize=14, color="#ffffff")
        ax.xaxis.set_major_locator(mdates.DayLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        fig.autofmt_xdate(rotation=45)
        ax.grid(True, color="#333333", linestyle="--", linewidth=0.7)
        ax.set_facecolor("#0f0f0f")
        ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
        plt.tight_layout()

        buf = BytesIO()
        plt.savefig(buf, format="png", dpi=800, facecolor=fig.get_facecolor())
        buf.seek(0)
        plt.close()

        file = nextcord.File(fp=buf, filename="stats.png")
        embed = nextcord.Embed(title=f"Activity Stats for {member.display_name}", color=nextcord.Color.blue())
        embed.set_image(url="attachment://stats.png")
        await interaction.followup.send(embed=embed, file=file)

def setup(bot):
    bot.add_cog(Stats(bot))
