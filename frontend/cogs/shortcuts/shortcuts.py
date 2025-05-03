import nextcord
from nextcord.ext import commands
from nextcord import SlashOption, Embed
from data import Data
from utilities import requires_owner, blacklist_check
import re

db = Data.database
shortcuts_collection = db["shortcuts"]

def strip_brackets(text: str) -> str:
    return re.sub(r"[\[\]]", "", text)

class Shortcuts(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="shortcut", description="Manage shortcuts for reasoning.")
    @requires_owner()
    @blacklist_check()
    async def shortcut(self, interaction: nextcord.Interaction):
        pass  # placehold

    @shortcut.subcommand(name="add", description="Add a new shortcut.")
    @requires_owner()
    @blacklist_check()
    async def add(
        self,
        interaction: nextcord.Interaction,
        keyword: str = SlashOption(
            name="keyword",
            description="The [keyword] to trigger the shortcut."
        ),
        value: str = SlashOption(
            name="value",
            description="The value that replaces the keyword."
        )
    ):
        clean_keyword = strip_brackets(keyword).strip()
        clean_value = strip_brackets(value).strip()

        shortcuts_collection.update_one(
            {"keyword": clean_keyword},
            {"$set": {"value": clean_value}},
            upsert=True
        )

        embed = Embed(
            title="Shortcut Added",
            color=nextcord.Color.green()
        )
        embed.add_field(name="Keyword", value=f"`[{clean_keyword}]`", inline=False)
        embed.add_field(name="Value", value=f"```{clean_value}```", inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=False)

    @shortcut.subcommand(name="remove", description="Remove an existing shortcut.")
    @requires_owner()
    @blacklist_check()
    async def remove(
        self,
        interaction: nextcord.Interaction,
        keyword: str = SlashOption(
            name="keyword",
            description="The [keyword] to remove."
        )
    ):
        clean_keyword = strip_brackets(keyword).strip()

        result = shortcuts_collection.delete_one({"keyword": clean_keyword})
        if result.deleted_count == 0:
            embed = Embed(
                title="Shortcut Not Found",
                description=f"No shortcut found with keyword `{clean_keyword}`.",
                color=nextcord.Color.red()
            )
        else:
            embed = Embed(
                title="Shortcut Removed",
                description=f"The shortcut for `{clean_keyword}` has been deleted.",
                color=nextcord.Color.orange()
            )

        await interaction.response.send_message(embed=embed, ephemeral=False)

    @shortcut.subcommand(name="list", description="List all available shortcuts.")
    @requires_owner()
    @blacklist_check()
    async def list(
        self,
        interaction: nextcord.Interaction
    ):
        shortcuts = shortcuts_collection.find() 
        shortcut_list = [f"`[{doc['keyword']}]` → `{doc['value']}`" for doc in shortcuts]

        embed = Embed(
            title="Available Shortcuts",
            color=nextcord.Color.blue()
        )

        if not shortcut_list:
            embed.description = "No shortcuts have been added yet."
        else:
            content = "\n".join(shortcut_list)
            if len(content) > 4000:
                content = content[:4000] + "\n...and more"
            embed.description = content

        await interaction.response.send_message(embed=embed, ephemeral=False)

def setup(bot):
    bot.add_cog(Shortcuts(bot))

