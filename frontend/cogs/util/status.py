import nextcord
from nextcord.ext import commands
from utilities import requires_owner

class Status(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="setstatus", description="Change the bot's status.")
    @requires_owner()
    async def setstatus(
        self,
        interaction: nextcord.Interaction,

        activity_type: str = nextcord.SlashOption(
            name="type",
            description="Type of status to set",
            choices={
                "Playing": "playing",
                "Listening": "listening",
                "Watching": "watching"
            }
        ),

        text: str = nextcord.SlashOption(
            description="The text for the status (e.g., name of the game, stream title, etc.)"
        )
    ):
        activity = None

        if activity_type == "playing":
            activity = nextcord.Game(name=text)
        elif activity_type == "listening":
            activity = nextcord.Activity(type=nextcord.ActivityType.listening, name=text)
        elif activity_type == "watching":
            activity = nextcord.Activity(type=nextcord.ActivityType.watching, name=text)

        await self.bot.change_presence(activity=activity)
        await interaction.response.send_message(f"Status updated to {activity_type.title()} {text}", ephemeral=True)

def setup(bot):
    bot.add_cog(Status(bot))
