import nextcord
from nextcord.ext import commands
import psutil
import platform
import time
import requests
from utility import logger
from main import local_version
from utilities import SystemConfig, blacklist_check

system_config = SystemConfig.system_config
start_time = time.time()


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def format_command(self, command, depth=0):
        indent = " " * depth
        arrow = "➤" if depth == 0 else "↳"
        name = getattr(command, "name", str(command))
        output = f"{indent}{arrow} /{name}"

        if hasattr(command, "children"):
            for subcommand in command.children:
                output += "\n" + self.format_command(subcommand, depth + 1)
        elif hasattr(command, "options"):
            for opt in command.options:
                if hasattr(opt, "type") and opt.type in [1, 2]:
                    output += "\n" + self.format_command(opt, depth + 1)
                elif hasattr(opt, "name"):
                    output += f" <{opt.name}>"
                else:
                    output += f" <{str(opt)}>"

        return output


    # This command will give helpful information about the bot
    @nextcord.slash_command(name="help", description="View important bot information.")
    @blacklist_check()
    async def help(self, interaction: nextcord.Interaction):
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            ram = psutil.virtual_memory()
            ram_percent = ram.percent
            total_ram_gb = round(ram.total / (1024 ** 3), 2)

            disk = psutil.disk_usage('/')
            disk_percent = disk.percent

            cores = psutil.cpu_count(logical=False)
            threads = psutil.cpu_count(logical=True)

            current_time = time.time()
            uptime_seconds = int(current_time - start_time)
            uptime_timestamp = int(current_time - uptime_seconds)
            discord_timestamp = f"<t:{uptime_timestamp}:R>"

            # Stores the command list here
            command_list = ""
            for command in self.bot.get_application_commands():
                try:
                    command_list += self.format_command(command) + "\n"
                except Exception as e:
                    logger.error(f"Error formatting command: {command} | Exception: {e}")
                    command_list += f"➤ /{getattr(command, 'name', str(command))} (error)\n"

            embed = nextcord.Embed(
                title=f"{system_config['discord']['bot_name']} v{local_version}",
                url="https://github.com/qonyx1/scambanner",
                description=f"**Commands:**\n```{command_list}```",
                color=nextcord.Color.green()
            )

            # CPU Info ???
            embed.add_field(name="CPU Usage", value=f"{cpu_percent}%", inline=True)

            # RAM/Core Info
            embed.add_field(name="RAM Usage", value=f"{ram_percent}%", inline=True)
            embed.add_field(name="Disk Usage", value=f"{disk_percent}%", inline=True)
            embed.add_field(name="Installed RAM", value=f"{total_ram_gb} GB", inline=True)
            embed.add_field(name="Cores / Threads", value=f"{cores} cores / {threads} threads", inline=True)

            # System Info
            embed.add_field(name="Uptime", value=discord_timestamp, inline=False)


            embed.set_footer(
                text=f"Running on Python {platform.python_version()} | {platform.system()} {platform.release()}"
            )

            await interaction.response.send_message(embed=embed)

            try:
                url = "https://raw.githubusercontent.com/qonyx1/scambanner/refs/heads/main/.VERSION"
                version = requests.get(url=url).text

                if version != local_version:
                    await interaction.followup.send(
                        embed = nextcord.Embed(
                            title = "System Outdated",
                            description = f"The bot's version is not up-to-date with the latest release of [Scambanner](https://github.com/qonyx1/scambanner) ({str(version)}). Please reach out to the owner of this bot to update immediately.",
                            color = nextcord.Color.orange()
                        )
                    )
            except Exception as e:
                logger.error(f"Error fetching version: {e}")
                version = "NaN"

        except Exception as e:
            logger.error(f"Help command failed: {e}")
            await interaction.response.send_message("Something went wrong while generating the help menu.", ephemeral=True)


def setup(bot):
    bot.add_cog(Help(bot))
