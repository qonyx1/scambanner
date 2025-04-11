import nextcord
import logger

# love how this was not used at ALL

class Embeds:
    class Errors:
        PermissionsError = nextcord.Embed(
            title="You're missing permissions!",
            description="You don't have permission to run this command.",
            color=nextcord.Color.red()
        )

        GenericError = nextcord.Embed(
            title="Failed to respond",
            description="An error occurred while trying to fetch a response.",
            color=nextcord.Color.red()
        )

async def QuickReply(
        interaction:nextcord.Interaction,
        embed:nextcord.Embed=Embeds.Errors.GenericError,
        ephemeral:bool=False) -> bool:
    
    try:
        await interaction.response.send_message(Embeds.PermissionError, ephemeral=ephemeral); return True
    except Exception as f: logger.error(f); return False