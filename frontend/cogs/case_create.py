import re
import nextcord, requests
from nextcord.ext import commands
from nextcord.ui import View, Button
from utilities import SystemConfig
from utility import logger
from data import Data
import asyncio

system_config = SystemConfig.system_config

def build_case_embed(responsible_guild, accused, investigator, created_at, reason, proof_links):
    embed = nextcord.Embed(
        title=f"📜 Case from {responsible_guild.name} ({responsible_guild.id})",
        color=nextcord.Color.orange()
    )
    embed.add_field(
        name="🧑‍⚖️ Accused",
        value=f"{accused.name} ({accused.id})" if accused != "NaN" else "NaN",
        inline=False
    )
    embed.add_field(
        name="🔍 Investigator",
        value=f"{investigator.name} ({investigator.id})" if investigator != "NaN" else "NaN",
        inline=False
    )
    embed.add_field(
        name="⏳ Time",
        value=f"<t:{int(created_at.timestamp())}:F>",
        inline=False
    )
    embed.add_field(
        name="📌 Reason",
        value=f"```{reason}```",
        inline=False
    )
    if proof_links:
        embed.add_field(
            name="🖼 Proof",
            value="\n".join(proof_links),
            inline=False
        )
    return embed

class ConfirmCancelView(View):
    def __init__(self, bot, message, accused_id, reason, proof_links):
        super().__init__(timeout=None)
        self.bot = bot
        self.message = message
        self.accused_id = accused_id
        self.reason = reason
        self.proof_links = proof_links

    @nextcord.ui.button(label="Confirm", style=nextcord.ButtonStyle.green, custom_id="confirm_case")
    async def confirm(self, button: Button, interaction: nextcord.Interaction):
        if interaction.user != self.message.author:
            await interaction.response.send_message("You can't confirm someone else's case!", ephemeral=True)
            return
        await self.message.clear_reactions()
        await self.message.add_reaction("⚖️")
        await interaction.message.delete()
        await self.submit_case_to_queue(interaction)

    @nextcord.ui.button(label="Cancel", style=nextcord.ButtonStyle.red, custom_id="cancel_case")
    async def cancel(self, button: Button, interaction: nextcord.Interaction):
        if interaction.user != self.message.author:
            await interaction.response.send_message("You can't cancel someone else's case!", ephemeral=True)
            return
        await self.message.clear_reactions()
        await self.message.add_reaction("🔒")
        await interaction.message.delete()

    async def submit_case_to_queue(self, interaction):
        queue_channel = self.bot.get_channel(int(system_config["discord"]["main_channel_id"]))
        if queue_channel:
            try:
                accused = await self.bot.fetch_user(int(self.accused_id))
            except Exception:
                accused = "NaN"
            investigator = self.message.author
            responsible_guild = self.message.guild
            case_embed = build_case_embed(
                responsible_guild,
                accused,
                investigator,
                self.message.created_at,
                self.reason,
                self.proof_links
            )
            review_view = CaseReviewView(self.bot, case_embed, self.accused_id, self.reason, self.proof_links, responsible_guild)
            sent_message = await queue_channel.send(embed=case_embed, view=review_view)
            review_view.message = sent_message

class CaseReviewView(View):
    def __init__(self, bot, embed, accused_id, reason, proof_links, responsible_guild):
        super().__init__(timeout=None)
        self.bot = bot
        self.embed = embed
        self.message = None
        self.accused_id = accused_id
        self.reason = reason
        self.proof_links = proof_links
        self.responsible_guild = responsible_guild

    async def disable_buttons_and_update_embed(self, interaction, decision: str):
        for child in self.children:
            child.disabled = True
        if decision == "approve":
            self.embed.color = nextcord.Color.green()
            self.embed.title = f"⚖️ Approved - *{self.responsible_guild.name}* (**{self.responsible_guild.id}**)"
        elif decision == "reject":
            self.embed.color = nextcord.Color.red()
            self.embed.title = f"🔒 Rejected - *{self.responsible_guild.name}* (**{self.responsible_guild.id}**)"
        self.embed.set_footer(text=f"Reviewed by {interaction.user.name} ({interaction.user.id})")
        await interaction.message.edit(embed=self.embed, view=None)

    @nextcord.ui.button(label="Approve", style=nextcord.ButtonStyle.green, custom_id="approve_case")
    async def approve(self, button: Button, interaction: nextcord.Interaction):
        await self.disable_buttons_and_update_embed(interaction, "approve")
        await interaction.response.defer()
        accused_id = int(self.accused_id)
        payload = {
            "master_password": system_config["api"]["master_password"],
            "server_id": self.responsible_guild.id,
            "accused_member": accused_id,
            "investigator_member": interaction.user.id,
            "reason": self.reason,
            "proof": self.proof_links
        }
        try:
            create_request = requests.post(
                url=f"http://127.0.0.1:{system_config['api']['port']}/cases/create_case",
                json=payload
            )
            if create_request.status_code != 200:
                await interaction.followup.send("Failed to communicate with the database (non-200 response).", ephemeral=True)
                return
            response_json = create_request.json()
            if response_json is None or "case_data" not in response_json:
                await interaction.followup.send("Failed to create the case in the database.", ephemeral=True)
                return
            case_data = response_json.get("case_data")
            case_id = case_data.get("case_id")
            if case_id:
                await interaction.followup.send(f"This case has been approved and created with the Case ID: **{case_id}**", ephemeral=True)
                
            else:
                await interaction.followup.send("Case creation failed. No case ID returned.", ephemeral=True)
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to submit the case: {e}")
            await interaction.followup.send("Failed to submit the case to the database.", ephemeral=True)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            await interaction.followup.send("An unexpected error occurred while processing the case.", ephemeral=True)

    @nextcord.ui.button(label="Reject", style=nextcord.ButtonStyle.red, custom_id="reject_case")
    async def reject(self, button: Button, interaction: nextcord.Interaction):
        await interaction.response.send_message("Case rejected.", ephemeral=True)
        await self.disable_buttons_and_update_embed(interaction, "reject")

class CaseCreation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.guild_channel_cache = []
        self.cooldown = {}

    @commands.Cog.listener()
    async def on_ready(self):
        pass

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild and not message.author.bot:
            current_time = message.created_at.timestamp()
            user_id = message.author.id
            if user_id in self.cooldown:
                last_sent = self.cooldown[user_id]
                if current_time - last_sent < 5:
                    await message.delete()
                    return
            self.cooldown[user_id] = current_time
            whitelist_entry = Data.database["bot"]["whitelists"].find_one({str(message.guild.id): {"$exists": True}})
            if whitelist_entry:
                channel_id = whitelist_entry.get(str(message.guild.id))
                if channel_id and int(channel_id) == message.channel.id:
                    if message.channel.id not in self.guild_channel_cache:
                        self.guild_channel_cache.append(message.channel.id)
                    content = message.content.strip()
                    if content.startswith("```") and content.endswith("```"):
                        content = content.strip("`").replace("```", "", 1)
                    pattern = r"Accused Discord ID:\s*(\d+)\s*\nReason:\s*(.+?)\s*\nProof:\s*((?:https?:\/\/\S+\s*)+)"
                    match = re.search(pattern, content, re.DOTALL)
                    if match:
                        accused_id = match.group(1)
                        reason = match.group(2).strip()
                        proof_links = [link.strip() for link in match.group(3).split("\n") if link.strip()]
                        if not accused_id or not reason or not proof_links:
                            return
                        logger.output(f"New case created: Accused ID: {accused_id}, Reason: {reason}, Proof: {proof_links}")
                        try:
                            accused = await self.bot.fetch_user(int(accused_id))
                        except Exception:
                            accused = "NaN"
                        investigator = message.author
                        responsible_guild = message.guild
                        confirmation_embed = build_case_embed(
                            responsible_guild,
                            accused,
                            investigator,
                            message.created_at,
                            reason,
                            proof_links
                        )
                        confirmation_embed.title = "Confirm Case Submission"
                        confirmation_embed.set_footer(text="After confirming, this case will be reviewed by our quality assurance team.")
                        qa_view = ConfirmCancelView(self.bot, message, accused_id, reason, proof_links)
                        self.bot.add_view(qa_view)
                        await message.channel.send(embed=confirmation_embed, view=qa_view)
                    else:
                        await message.channel.send(
                            embed=nextcord.Embed(
                                title="Invalid Case Format",
                                description="**Please use the correct format:**\n```\nAccused Discord ID: 123456789\nReason: <reason>\nProof:\nhttps://example.com\nhttps://example.com\n```",
                                color=nextcord.Color.red()
                            )
                        )
                        logger.error(f"Invalid case format detected in message ID {message.id}.")

def setup(bot):
    bot.add_cog(CaseCreation(bot))
