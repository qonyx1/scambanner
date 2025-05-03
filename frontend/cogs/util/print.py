import nextcord
from nextcord.ext import commands
from utility import logger
from utilities import requires_owner, SystemConfig, blacklist_check

system_config = SystemConfig.system_config

class Log(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="log", description="Log something to the server console.")
    @requires_owner()
    @blacklist_check()
    async def log(self,
                  interaction: nextcord.Interaction,

                  message: str = nextcord.SlashOption(
                      description="The message to send to the console."
                    ),

                  style: str = nextcord.SlashOption(
                        name="style",
                        description="The style in which the message will be displayed.",
                        choices={
                            "OK": "ok",
                            "OUTPUT": "output",
                            "WARNING": "warn",
                            "ERROR": "error"
                        }
                    )
                ):
        
        # ----- Command code -----

        style_map = {
            "ok": logger.ok,
            "output": logger.output,
            "warn": logger.warn,
            "error": logger.error
        }

        log_func = style_map.get(style, logger.output)
        log_func(message)

        await interaction.response.send_message("Logged to console!", ephemeral=True)

def setup(bot):
    bot.add_cog(Log(bot))
