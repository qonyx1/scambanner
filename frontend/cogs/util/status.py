import nextcord
from nextcord.ext import commands
from utilities import requires_owner

class Status(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="setstatus", description="Change the bot's status and activity.")
    @requires_owner()
    async def setstatus(
        self,
        interaction: nextcord.Interaction,
        activity_type: str = nextcord.SlashOption(
            name="type",
            description="Type of activity",
            choices={
                "Playing": "playing",
                "Listening": "listening",
                "Watching": "watching",
                "Streaming": "streaming"
            }
        ),
        status_text: str = nextcord.SlashOption(
            name="text",
            description="Text for the activity (you can use $members or $guilds)"
        ),
        status_mode: str = nextcord.SlashOption(
            name="status",
            description="Bot's online status",
            choices={
                "Online": "online",
                "Idle": "idle",
                "Do Not Disturb": "dnd"
            }
        )
    ):
        total_members = sum(guild.member_count for guild in self.bot.guilds)
        total_guilds = len(self.bot.guilds)
        final_text = status_text.replace("$members", str(total_members)).replace("$guilds", str(total_guilds))

        if activity_type == "playing":
            activity = nextcord.Game(name=final_text)
        elif activity_type == "listening":
            activity = nextcord.Activity(type=nextcord.ActivityType.listening, name=final_text)
        elif activity_type == "watching":
            activity = nextcord.Activity(type=nextcord.ActivityType.watching, name=final_text)
        elif activity_type == "streaming":
            activity = nextcord.Streaming(name=final_text, url="https://twitch.tv/yourchannel")

        status_map = {
            "online": nextcord.Status.online,
            "idle": nextcord.Status.idle,
            "dnd": nextcord.Status.dnd
        }

        await self.bot.change_presence(status=status_map[status_mode], activity=activity)
        await interaction.response.send_message(
            f"Bot status updated:\n**{activity_type.title()}** {final_text}\n**Status:** {status_mode.title()}",
            ephemeral=True
        )

def setup(bot):
    bot.add_cog(Status(bot))
