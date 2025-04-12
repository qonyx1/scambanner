import nextcord
from nextcord.ext import commands
from utilities import requires_owner
import subprocess
import sys
import hashlib, os

class Update(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="update", description="Update the bot to the latest version available.")
    @requires_owner()
    async def update(self, interaction: nextcord.Interaction, restart: bool):
        frontend_checksum = self.get_checksum("../frontend")
        backend_checksum = self.get_checksum("../backend")
        
        if restart:
            await interaction.response.send_message(
                embed=nextcord.Embed(
                    title="Bot Updating & Restarting",
                    description="The bot will automatically come online again. If it doesn't, the bot has errored.",
                    color=nextcord.Color.orange()
                ).add_field(
                    name="Frontend Checksum", value=frontend_checksum, inline=False
                ).add_field(
                    name="Backend Checksum", value=backend_checksum, inline=False
                )
            )
            self.run_update_script("../update_and_run_bot_vers.sh")
        else:
            await interaction.response.send_message(
                embed=nextcord.Embed(
                    title="Updating Source Code",
                    description="Downloading and replacing the current bot tree, please wait.",
                    color=nextcord.Color.orange()
                ).add_field(
                    name="Frontend Checksum", value=frontend_checksum, inline=False
                ).add_field(
                    name="Backend Checksum", value=backend_checksum, inline=False
                )
            )
            self.run_update_script("../update_bot_vers.sh")

    def run_update_script(self, script_path: str):
        if sys.platform == "win32":
            DETACHED_PROCESS = 0x00000008
            subprocess.Popen(["bash", script_path], creationflags=DETACHED_PROCESS)
        else:
            subprocess.Popen(
                ["bash", script_path],
                start_new_session=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
            )

    def get_checksum(self, directory_path: str):
        hash_md5 = hashlib.md5()
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                with open(os.path.join(root, file), "rb") as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        hash_md5.update(chunk)
        return hash_md5.hexdigest()


def setup(bot):
    bot.add_cog(Update(bot))
