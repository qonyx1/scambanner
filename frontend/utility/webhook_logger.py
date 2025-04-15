import os
import requests
import nextcord
from dotenv import load_dotenv
from utility import logger

load_dotenv()

async def log(title: str, description: str, color: int, fields: list, footer: str = None):
    webhook_url = os.getenv("WEBHOOK_URL")
    
    if not webhook_url:
        logger.error("[WEBHOOK_LOGGER] WEBHOOK IS NOT SET WITHIN ENV, API KEYS HAVE FREE REIGN WITHOUT LOGS")
        return False
    
    embed = {
        "embeds": [{
            "title": title,
            "description": description,
            "color": color,
            "fields": [{"name": field[0], "value": field[1]} for field in fields],
            "footer": {"text": footer} if footer else {}
        }]
    }
    
    response = requests.post(webhook_url, json=embed)
    
    if response.status_code != 204:
        logger.error(f"[WEBHOOK_LOGGER] Failed to send message to webhook. Status code: {response.status_code}, Response: {response.text}")
        return True
    else:
        logger.ok(f"[WEBHOOK_LOGGER] Message sent successfully to webhook. Status code: {response.status_code}")
        return False


async def log_object(embed: nextcord.Embed):
    """
    Accepts a nextcord Embed object and sends it to the configured webhook.
    """
    webhook_url = os.getenv("WEBHOOK_URL")
    
    if not webhook_url:
        logger.error("[WEBHOOK_LOGGER] WEBHOOK IS NOT SET WITHIN ENV, API KEYS HAVE FREE REIGN WITHOUT LOGS")
        return False
    
    embed_dict = embed.to_dict()
    payload = {"embeds": [embed_dict]}
    
    response = requests.post(webhook_url, json=payload)
    
    if response.status_code != 204:
        logger.error(f"[WEBHOOK_LOGGER] Failed to send message to webhook. Status code: {response.status_code}, Response: {response.text}")
        return True
    else:
        logger.ok(f"[WEBHOOK_LOGGER] Message sent successfully to webhook. Status code: {response.status_code}")
        return False
