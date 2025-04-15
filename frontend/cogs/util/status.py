import nextcord
from nextcord.ext import commands
from utilities import requires_owner

class Status(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        total_members = sum(guild.member_count or 0 for guild in self.bot.guilds)
        formatted_members = f"{total_members:,}"
        activity = nextcord.Activity(
            type=nextcord.ActivityType.watching,
            name=f"over {formatted_members} members"
        )
        await self.bot.change_presence(status=nextcord.Status.dnd, activity=activity)

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
                "Watching": "watching"
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
        total_members = sum(guild.member_count or 0 for guild in self.bot.guilds)
        total_guilds = len(self.bot.guilds)
        formatted_members = f"{total_members:,}"
        formatted_guilds = f"{total_guilds:,}"
        
        final_text = status_text.replace("$members", formatted_members).replace("$guilds", formatted_guilds)

        if activity_type == "playing":
            activity = nextcord.Game(name=final_text)
        elif activity_type == "listening":
            activity = nextcord.Activity(type=nextcord.ActivityType.listening, name=final_text)
        elif activity_type == "watching":
            activity = nextcord.Activity(type=nextcord.ActivityType.watching, name=final_text)

        status_map = {
            "online": nextcord.Status.online,
            "idle": nextcord.Status.idle,
            "dnd": nextcord.Status.dnd
        }

        pretty_status = "DND" if status_mode == "dnd" else status_mode.title()

        colors = {
            nextcord.Status.online: nextcord.Color.green(),
            nextcord.Status.idle: nextcord.Color.orange(),
            nextcord.Status.dnd: nextcord.Color.red()
        }

        embed = nextcord.Embed(
            title="Bot Status Updated",
            color=colors[status_map[status_mode]]
        )
        embed.add_field(name="Activity", value=activity_type.title())
        embed.add_field(name="Status", value=pretty_status)
        embed.add_field(name="Text", value=final_text)

        await self.bot.change_presence(status=status_map[status_mode], activity=activity)
        await interaction.response.send_message(
            embed=embed,
            ephemeral=False
        )

def setup(bot):
    bot.add_cog(Status(bot))
