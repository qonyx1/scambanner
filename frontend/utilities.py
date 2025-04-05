import uuid
import tomli
import base64, random, string
from typeguard import typechecked
from functools import wraps
from nextcord import Interaction, Member
from nextcord.ext.commands.errors import CheckFailure

class SystemConfig:
    with open("../system_config.toml", mode="rb") as fp:
        system_config = tomli.load(fp) or None

def requires_owner() -> None:
    def decorator(func):
        @wraps(func)
        async def wrapper(self, interaction: Interaction, *args, **kwargs):
            member: Member = interaction.user
            if member.id in SystemConfig.system_config.get("discord", {}).get("additional_owners", []):
                return await func(self, interaction, *args, **kwargs)
            else:
                await interaction.response.send_message(
                    "*You do not have permission to use this command.*",
                    ephemeral=True
                )
                return
        return wrapper
    return decorator