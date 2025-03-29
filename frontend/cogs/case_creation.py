import nextcord, requests
from data import Data
import json
from utilities import SystemConfig
system_config = SystemConfig.system_config
url = system_config["api"]["url"]

from nextcord.ext import commands
from cogs.case_delete_and_view import Cases

class CaseCreation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # TODO: Make http://ip:port sync with settings
    # @Cases.case.subcommand(name="config", description="Fetch a case from the database.")
    # async def asd(self, interaction, caseid: str = nextcord.SlashOption(
    #     name="caseid",
    #     description="Select a case ID",
    #     choices=["case1", "case2", "case3"]
    # )):
    #     print("hi")

def setup(bot):
    bot.add_cog(CaseCreation(bot))
