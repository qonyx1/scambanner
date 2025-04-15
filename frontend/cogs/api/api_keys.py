import nextcord
from nextcord.ext import commands
import secrets, string, time
from generateApiKey import generateApiKey
from utilities import requires_owner, SystemConfig
from data import Data
import re

db = Data.database
system_config = SystemConfig.system_config

# Generate a secure API key
async def getRandomApiKey():
    rand = lambda n: ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(n))
    return await generateApiKey(rand(24), rand(12), prefix='sb', add_dashes=True)

# Convert bool to emoji
def turn(v: bool):
    return "✅" if v else "❌"

# Parse "1/h", "5/s", "10/m", etc. into (max_requests, time_window) based on regex pattern
def parse_rate_limit(rate_str: str):
    # Clean and match the rate string format
    match = re.match(r"(\d+)\s*/\s*([smhd])", rate_str.strip().lower())
    if match:
        count = int(match.group(1))
        unit = match.group(2)
        time_multipliers = {
            "s": 1,      # seconds
            "m": 60,     # minutes
            "h": 3600,   # hours
            "d": 86400   # days
        }

        # Calculate the time window based on the unit
        time_window = time_multipliers[unit]

        # If count is 1, we interpret it as 1 request per the time window
        return count, time_window

    # If no match found, raise an exception
    raise ValueError(f"Invalid rate limit format: {rate_str}")

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
            # Parse the ratelimit input (this will not default to 60 if it's invalid)
            max_requests, time_window = parse_rate_limit(ratelimit)
        except ValueError as e:
            # If there is an error parsing the rate limit, respond with an error
            await interaction.response.send_message(f"Error parsing rate limit: {str(e)}", ephemeral=True)
            return

        # Setup the rate limit dictionary for the API key
        ratelimit_dict = {
            "max_requests": max_requests,
            "time_window": time_window,
            "last_request_time": int(time.time()),
            "request_count": 0
        }

        # Generate the API key
        key = await getRandomApiKey()
        db["keys"].find_one_and_delete({"_id": key})

        # Insert the new API key into the database
        db["keys"].insert_one({
            "_id": key,
            "create_case": create_case,
            "fetch_case": fetch_case,
            "delete_case": delete_case,
            "case_dump": case_dump,
            "ratelimit": ratelimit_dict,
        })

        # Fetch the newly inserted API key info
        info = db["keys"].find_one({"_id": key})
        embed = nextcord.Embed(
            title="API Key Generated",
            description=f"This key has been generated, make sure nobody is watching!\n`{key}`",
            color=nextcord.Color.green()
        )

        # Add the permissions to the embed
        for perm_key, description in {
            "create_case": "Create Case",
            "fetch_case": "Fetch Case",
            "delete_case": "Delete Case",
            "case_dump": "Case Dump"
        }.items():
            value = info.get(perm_key, False)
            embed.add_field(name=description, value=turn(value), inline=True)

        # Format rate limit for embed
        rl = info.get("ratelimit", {})
        if isinstance(rl, dict):
            rl_text = f"Max Requests: {rl.get('max_requests', 'N/A')}\nTime Window: {rl.get('time_window', 'N/A')} seconds"
        else:
            rl_text = str(rl)

        embed.add_field(name="Ratelimit", value=rl_text, inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @api_key.subcommand(name="list", description="List all API keys and their permissions.")
    @commands.cooldown(1, 10, commands.BucketType.user)
    @requires_owner()
    async def list_keys(self, interaction: nextcord.Interaction):
        keys = list(db["keys"].find({}))
        if not keys:
            await interaction.response.send_message("No API keys found.", ephemeral=True)
            return

        embed = nextcord.Embed(
            title="Stored API Keys",
            description="Permissions and rate limits listed below. Raw keys will be sent separately.",
            color=nextcord.Color.blurple()
        )

        key_lines = []

        for idx, key_info in enumerate(keys[:10], start=1):  # Limit shown keys
            key = key_info.get("_id", "N/A")
            perms = []
            for perm, label in {
                "create_case": "🆕 Create",
                "fetch_case": "📄 Fetch",
                "delete_case": "❌ Delete",
                "case_dump": "📦 Dump"
            }.items():
                if key_info.get(perm, False):
                    perms.append(label)

            perm_text = ", ".join(perms) if perms else "None"

            rl = key_info.get("ratelimit", {})
            rl_summary = "None"
            if isinstance(rl, dict):
                rl_summary = f"{rl.get('max_requests', '?')} req / {rl.get('time_window', '?')}s"

            embed.add_field(
                name=f"API Key #{idx}",
                value=f"Permissions: {perm_text}\nRate Limit: {rl_summary}",
                inline=False
            )

            key_lines.append(f"{idx}. `{key}`")

        await interaction.response.send_message(embed=embed, ephemeral=True)

        keys_text = "**API Keys:**\n" + "\n".join(key_lines)
        await interaction.followup.send(content=keys_text, ephemeral=True)

    @api_key.subcommand(name="delete", description="Delete an API key.")
    @commands.cooldown(1, 10, commands.BucketType.user)
    @requires_owner()
    async def delete(self, interaction: nextcord.Interaction, key: str):
        info = db["keys"].find_one({"_id": key})
        if not info:
            await interaction.response.send_message("API key not found.", ephemeral=True)
            return

        db["keys"].find_one_and_delete({"_id": key})

        embed = nextcord.Embed(
            title="API Key Deleted",
            description=f"The API key has been deleted!\n`{key}`",
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

        await interaction.response.send_message(embed=embed, ephemeral=True)

def setup(bot):
    bot.add_cog(Keys(bot))
