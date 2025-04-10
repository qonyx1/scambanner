import nextcord
from nextcord.ext import commands
import secrets, string, time
from generateApiKey import generateApiKey
from utilities import requires_owner, SystemConfig
from data import Data

db = Data.database
system_config = SystemConfig.system_config

async def getRandomApiKey():
    rand = lambda n: ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(n))
    return await generateApiKey(rand(24), rand(12), prefix='sb', add_dashes=True)

def turn(v: bool):
    return "✅" if v else "❌"

class Keys(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="api_key", description="Generate API keys.")
    @requires_owner()
    async def api_key(self, interaction: nextcord.Interaction):
        return

    @api_key.subcommand(name="generate", description="Generate an API key with certain permissions.")
    @commands.cooldown(1, 10, commands.BucketType.user)
    @requires_owner()
    async def generate(
        self,
        interaction: nextcord.Interaction,
        create_case: bool,
        fetch_case: bool,
        delete_case: bool,
        case_dump: bool,
        ratelimit: str
    ):
        try:
            max_requests = int(ratelimit)
        except ValueError:
            max_requests = 2

        ratelimit_dict = {
            "max_requests": max_requests,
            "time_window": 60,
            "last_request_time": int(time.time()),
            "request_count": 0
        }

        key = await getRandomApiKey()
        db["keys"].find_one_and_delete({"_id": key})
        
        db["keys"].insert_one({
            "_id": key,
            "create_case": create_case,
            "fetch_case": fetch_case,
            "delete_case": delete_case,
            "case_dump": case_dump,
            "ratelimit": ratelimit_dict,
        })

        info = db["keys"].find_one({"_id": key})
        embed = nextcord.Embed(
            title="API Key Generated",
            description=f"This key has been generated, make sure nobody is watching!\n||`{key}`||",
            color=nextcord.Color.green()
        )

        for perm_key, description in {
            "create_case": "Create Case",
            "fetch_case": "Fetch Case",
            "delete_case": "Delete Case",
            "case_dump": "Case Dump"
        }.items():
            value = info.get(perm_key, False)
            embed.add_field(name=description, value=turn(value), inline=True)

        rl = info.get("ratelimit", {})
        if isinstance(rl, dict):
            rl_text = f"Max Requests: {rl.get('max_requests', 'N/A')}\nTime Window: {rl.get('time_window', 'N/A')} seconds"
        else:
            rl_text = str(rl)

        embed.add_field(name="Ratelimit", value=rl_text, inline=False)

        await interaction.response.send_message(embed=embed)

    @api_key.subcommand(name="delete", description="Delete an API key.")
    @commands.cooldown(1, 10, commands.BucketType.user)
    @requires_owner()
    async def delete(self, interaction: nextcord.Interaction, key: str):
        info = db["keys"].find_one({"_id": key})
        if not info:
            await interaction.response.send_message("API key not found.")
            return

        db["keys"].find_one_and_delete({"_id": key})

        embed = nextcord.Embed(
            title="API Key Deleted",
            description=f"The API key has been deleted!\n||`{key}`||",
            color=nextcord.Color.red()
        )

        for perm_key, description in {
            "create_case": "Create Case",
            "fetch_case": "Fetch Case",
            "delete_case": "Delete Case",
            "case_dump": "Case Dump"
        }.items():
            value = info.get(perm_key, False)
            embed.add_field(name=description, value=turn(value), inline=True)

        rl = info.get("ratelimit", {})
        if isinstance(rl, dict):
            rl_text = f"Max Requests: {rl.get('max_requests', 'N/A')}\nTime Window: {rl.get('time_window', 'N/A')} seconds"
        else:
            rl_text = str(rl)

        embed.add_field(name="Ratelimit", value=rl_text, inline=False)

        await interaction.response.send_message(embed=embed)

def setup(bot):
    bot.add_cog(Keys(bot))
