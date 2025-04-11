"""
Contains FRONTEND (Bot) code for case creation command(s).

Layout:
    - User from a whitelisted server/channel submits a case
    - Case template is sent to Quality Assurance team
    - Case template is reviewed and Approved or Denied
    - If approved, the case wil be submitted and sent over the backend (API)
"""

import re
import nextcord, requests
from nextcord.ext import commands
from nextcord.ui import View, Button
from utilities import SystemConfig, send_case_logs
from utility import logger
from data import Data
import asyncio
import datetime
import os
import tempfile
import aiohttp
from urllib.parse import urlparse
from utility import custom_uploads
from types import SimpleNamespace

system_config = SystemConfig.system_config

discord_cdn_domains = [
    "cdn.discordapp.com",
    "media.discordapp.net",
    "images-ext-1.discordapp.net"
]

async def download_file(url, dest_path):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    with open(dest_path, "wb") as f:
                        f.write(await resp.read())
                    return dest_path
                else:
                    return None
    except Exception as e:
        logger.error(f"Error downloading file {url}: {e}")
        return None

async def proxy_proof_links(proof_links):
    updated_proof_links = []
    temp_dir = tempfile.gettempdir()
    if system_config["api"].get("proof_proxy"):
        for link in proof_links:
            if any(domain in link for domain in discord_cdn_domains):
                filename = os.path.basename(urlparse(link).path)
                filepath = os.path.join(temp_dir, filename)
                downloaded_file = await download_file(link, filepath)
                if downloaded_file:
                    try:
                        if filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
                            new_link = custom_uploads.upload_image(downloaded_file)
                        elif filename.lower().endswith((".mp4", ".mov", ".avi")):
                            new_link = custom_uploads.upload_video(downloaded_file)
                        else:
                            continue
                        updated_proof_links.append(new_link)
                    except Exception as e:
                        logger.error(f"[UPLOAD_ERROR] Failed to upload {filename}: {e}")
                    finally:
                        os.remove(downloaded_file)
                else:
                    logger.error(f"[UPLOAD_ERROR] Failed to download proof file: {link}")
            else:
                updated_proof_links.append(link)
        return updated_proof_links
    else:
        return proof_links

def build_case_embed(responsible_guild, accused, investigator, created_at, reason, proof_links):
    if hasattr(investigator, "behalf_of"):
        inv_display = f"{investigator.name} ({investigator.id}) **(obh. {investigator.behalf_of})**"
    else:
        inv_display = f"{investigator.name} ({investigator.id})" if investigator != "NaN" else "NaN"
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
        value=inv_display,
        inline=False
    )
    embed.add_field(
        name="⏳ Time",
        value=f"<t:{int(created_at.timestamp())}:F>",
        inline=False
    )
    embed.add_field(
        name="📌 Reason",
        value=f"\n\n{reason}\n\n",
        inline=False
    )
    if proof_links:
        embed.add_field(
            name="🖼 Proof",
            value="\n".join(proof_links),
            inline=False
        )
    return embed

@staticmethod
async def main_log(self, embed: nextcord.Embed) -> bool:
    try:
        log_channel = int(system_config["discord"]["main_log_channel_id"])
        log_channel = await self.bot.fetch_channel(log_channel)
        await log_channel.send(embed=embed)
        return True
    except Exception as e:
        logger.error(f"Logging error: {e}")
        return False

class ConfirmCancelView(View):
    def __init__(self, bot, message, accused_id, reason, proof_links, investigator):
        super().__init__(timeout=None)
        self.bot = bot
        self.message = message
        self.accused_id = accused_id
        self.reason = reason
        self.proof_links = proof_links
        self.investigator = investigator

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
            investigator = self.investigator
            responsible_guild = self.message.guild
            processed_proof_links = await proxy_proof_links(self.proof_links)
            case_embed = build_case_embed(
                responsible_guild,
                accused,
                investigator,
                self.message.created_at,
                self.reason,
                processed_proof_links
            )
            review_view = CaseReviewView(self.bot, case_embed, self.accused_id, self.reason, processed_proof_links, responsible_guild, investigator)
            sent_message = await queue_channel.send(embed=case_embed, view=review_view)
            review_view.message = sent_message




class CaseReviewView(View):
    def __init__(self, bot, embed, accused_id, reason, proof_links, responsible_guild, investigator):
        super().__init__(timeout=None)
        self.bot = bot
        self.embed = embed
        self.message = None
        self.accused_id = accused_id
        self.reason = reason
        self.proof_links = proof_links
        self.responsible_guild = responsible_guild
        self.investigator = investigator

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
        try:
            role = await interaction.guild.fetch_role(system_config["discord"]["admin_team_role_id"])
            if role not in interaction.user.roles:
                return await interaction.response.send_message("*You need to be have the configured administrator role to use this!*")
        except:
            return await interaction.response.send_message("*I couldn't access the server's configured admin role.*")
        await self.disable_buttons_and_update_embed(interaction, "approve")
        await interaction.response.defer()
        accused_id = int(self.accused_id)
        payload = {
            "master_password": system_config["api"]["master_password"],
            "server_id": self.responsible_guild.id,
            "accused_member": accused_id,
            "investigator_member": self.investigator.id,
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
            await send_case_logs(self, case_id)
            accused_obj = await self.bot.fetch_user(accused_id)
            confirmation_embed = build_case_embed(
                self.responsible_guild,
                accused_obj,
                self.investigator,
                datetime.datetime.now(),
                self.reason,
                self.proof_links
            )
            await main_log(self=self, embed=confirmation_embed)
            await interaction.followup.send(f"This case has been approved and created with the Case ID: **{case_id}**", ephemeral=True)
            try:
                for guild in self.bot.guilds:
                    try:
                        v = await guild.fetch_member(accused_id)
                        await v.ban(reason=f"[CROSSBAN] via caseid {case_id}, created by investigator {self.investigator}")
                    except Exception:
                        pass
            except Exception as e:
                pass
            if not case_id:
                await interaction.followup.send("Case creation failed. No case ID returned.", ephemeral=True)
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to submit the case: {e}")
            await interaction.followup.send("Failed to submit the case to the database.", ephemeral=True)

    @nextcord.ui.button(label="Reject", style=nextcord.ButtonStyle.red, custom_id="reject_case")
    async def reject(self, button: Button, interaction: nextcord.Interaction):
        try:
            role = await interaction.guild.fetch_role(system_config["discord"]["admin_team_role_id"])
            if role not in interaction.user.roles:
                return await interaction.response.send_message("*You need to have the configured administrator role to use this!*")
        except:
            return await interaction.response.send_message("*I couldn't access the server's configured admin role.*")
        
        modal = RejectCaseModal(self.investigator, self.accused_id, self)
        await interaction.response.send_modal(modal)

class RejectDetailsView(nextcord.ui.View):
    def __init__(self, accused_id, investigator, reason, proof_links):
        super().__init__(timeout=None)
        self.accused_id = accused_id
        self.investigator = investigator
        self.reason = reason
        self.proof_links = proof_links

    @nextcord.ui.button(label="What was this?", style=nextcord.ButtonStyle.secondary, custom_id="details_button")
    async def what_was_this(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        details_embed = nextcord.Embed(
            title="📜 Case Rejection Details",
            color=nextcord.Color.red()
        )
        details_embed.add_field(name="🧑‍⚖️ Accused ID", value=str(self.accused_id), inline=False)
        if hasattr(self.investigator, "id"):
            investigator_id = self.investigator.id
        else:
            investigator_id = self.investigator
        details_embed.add_field(name="🔍 Investigator ID", value=str(investigator_id), inline=False)
        details_embed.add_field(name="📌 Reason", value=self.reason, inline=False)
        if self.proof_links:
            details_embed.add_field(name="🖼 Proof", value="\n".join(self.proof_links), inline=False)
        await interaction.response.send_message(embed=details_embed, ephemeral=True)

class RejectCaseModal(nextcord.ui.Modal):
    def __init__(self, investigator, accused_id, review_view: CaseReviewView):
        super().__init__(title="Reject Case", custom_id="reject_case_modal")
        self.investigator = investigator
        self.accused_id = accused_id
        self.review_view = review_view
        self.reason = nextcord.ui.TextInput(
            label="Reason for rejection", 
            style=nextcord.TextInputStyle.paragraph, 
            placeholder="Provide a reason for rejecting the case.", 
            required=True
        )
        self.add_item(self.reason)

    async def callback(self, interaction: nextcord.Interaction):
        reason = self.reason.value
        await self.review_view.disable_buttons_and_update_embed(interaction, "reject")
        await interaction.response.defer()
        self.review_view.embed.add_field(name="⛔ Rejection Reason", value=reason, inline=False)
        
        await interaction.message.edit(embed=self.review_view.embed, view=None)
        
        try:
            if hasattr(self.investigator, "id"):
                investigator_id = self.investigator.id
            else:
                investigator_id = int(self.investigator)
            inves = await self.review_view.bot.fetch_user(investigator_id)
            dm_embed = nextcord.Embed(
                title="⛔ Your case was rejected",
                description="A user on the Quality Assurance team has denied your case submission.",
                color=nextcord.Color.red()
            )
            dm_embed.add_field(name="🧑‍⚖️ Accused ID", value=str(self.accused_id), inline=True)
            dm_embed.add_field(name="📌 Reason", value=reason, inline=True)
            details_view = RejectDetailsView(
                accused_id=self.accused_id,
                investigator=self.investigator,
                reason=reason,
                proof_links=self.review_view.proof_links
            )
            await inves.send(embed=dm_embed, view=details_view)
        except Exception as e:
            logger.error(f"Failed to DM the investigator: {e}")
        
        logger.ok(f"Case rejected for accused {self.accused_id} by investigator {self.investigator}. Reason: {reason}", debug=True)

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
            guild_id_str = str(message.guild.id)

            whitelist_entry = Data.database["bot"]["whitelists"].find_one({guild_id_str: {"$exists": True}})
            if whitelist_entry:
                entry = whitelist_entry[guild_id_str]
                channel_id = entry.get("channel_id")
                role_id = entry.get("role_id")

                if channel_id and int(channel_id) == message.channel.id:
                    if role_id:
                        role = message.guild.get_role(int(role_id))
                        if role not in message.author.roles:
                            return  # User doesn't have the right role, ignore message

                    if message.channel.id not in self.guild_channel_cache:
                        self.guild_channel_cache.append(message.channel.id)

                    content = message.content.strip()
                    if content.startswith("") and content.endswith(""):
                        content = content.strip("").replace("", "", 1)

                    pattern = r"Accused Discord ID:\s*(\d+)\s*(?:\nInvestigator:\s*(\d+))?\s*\nReason:\s*(.+?)\s*\nProof:\s*((?:https?:\/\/\S+\s*)+)"
                    match = re.search(pattern, content, re.DOTALL)
                    if match:
                        accused_id = match.group(1)
                        investigator_id = match.group(2)
                        reason = match.group(3).strip()
                        proof_links = [link.strip() for link in match.group(4).split("\n") if link.strip()]
                        if not accused_id or not reason or not proof_links:
                            return

                        try:
                            req = requests.post(
                                url=f"http://127.0.0.1:{system_config['api']['port']}/checks/check_id",
                                json = {
                                        "accused_member": int(accused_id)
                                    }
                                )
                            if req.json().get("code") == 0:
                                caid = req.json().get("case_id")
                                x_embed = nextcord.Embed(
                                    title="User already has a case",
                                    description="Please delete this case from the database before making a new one.",
                                    color=nextcord.Color.red()
                                )
                                x_embed.add_field(name="Case ID", value=str(caid))

                                try:
                                    tmp = requests.post(
                                        url=f"http://127.0.0.1:{system_config['api']['port']}/cases/fetch_case",
                                        json = {
                                                "case_id": caid
                                            }
                                    )
                                    if tmp.json().get("case_data"):
                                        x_embed.add_field(name="Investigator",value=f"<@{tmp.json().get("case_data")["investigator"]}>")
                                        x_embed.add_field(name="Time",value=f"<t:{tmp.json().get("case_data")["created_at"]}>")
                                        x_embed.add_field(name="Reason",value=tmp.json().get("case_data")["reason"])
                                except:
                                    pass

                                await message.reply(embed=x_embed)
                                return
                        except Exception as e:
                            logger.error(e, debug=True)
                            pass
                        if investigator_id:
                            if int(investigator_id) != message.author.id:
                                try:
                                    fetched_investigator = await self.bot.fetch_user(int(investigator_id))
                                    investigator_final = SimpleNamespace(name=fetched_investigator.name, id=fetched_investigator.id, behalf_of=message.author.id)
                                except Exception:
                                    investigator_final = message.author
                            else:
                                investigator_final = message.author
                        else:
                            investigator_final = message.author
                        try:
                            accused = await self.bot.fetch_user(int(accused_id))
                        except Exception:
                            accused = "NaN"
                        responsible_guild = message.guild
                        confirmation_embed = build_case_embed(
                            responsible_guild,
                            accused,
                            investigator_final,
                            message.created_at,
                            reason,
                            proof_links
                        )
                        confirmation_embed.title = "Confirm Case Submission"
                        confirmation_embed.set_footer(text="After confirming, this case will be reviewed by our quality assurance team.")
                        qa_view = ConfirmCancelView(self.bot, message, accused_id, reason, proof_links, investigator_final)
                        self.bot.add_view(qa_view)
                        await message.reply(embed=confirmation_embed, view=qa_view)
                    else:
                        await message.reply(
                            embed=nextcord.Embed(
                                title="Invalid Case Format",
                                description="**Please use the correct format:**\n\nAccused Discord ID: 123456789\nInvestigator: 987654321 (optional)\nReason: <reason>\nProof:\nhttps://example.com\nhttps://example.com\n",
                                color=nextcord.Color.red()
                            )
                        )
                        logger.error(f"Invalid case format detected in message ID {message.id}.")

def setup(bot):
    bot.add_cog(CaseCreation(bot))
