import os
import time
import datetime
import logging
import nextcord
from urllib.parse import urlparse
from typing import List, Optional

import aiohttp, asyncio
import aiofiles
import tempfile
from fastapi import APIRouter, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from data import Data
from modules import custom_uploads, webhook_logger
from utilities import Generate, SystemConfig
import logger
from limiter import limiter  # limiter is defined inside `limiter.py`
import requests, httpx

import time
from datetime import timezone
from typing import Optional

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

system_config = SystemConfig.system_config
database = Data.database

class CaseID(BaseModel):
    case_id: str

class FetchCase(BaseModel):
    api_key: Optional[str] = None
    master_password: str
    case_id: str

class CreateCase(BaseModel):
    api_key: Optional[str] = None
    master_password: str
    server_id: int
    accused_member: int
    investigator_member: int
    reason: str
    proof: List[str] = []

class DumpCases(BaseModel):
    api_key: Optional[str] = None
    master_password: str

class DeleteCase(BaseModel):
    master_password: str
    api_key: Optional[str] = None
    case_id: str

allowed_paths = {
    "cdn.discordapp.com": "/attachments/",
    "media.discordapp.net": "/attachments/",
    "images-ext-1.discordapp.net": "/external/"
}

router = APIRouter(prefix="/cases", tags=["cases"])

async def build_case_embed(responsible_guild, accused, investigator, created_at, reason, proof_links, api_key=False):
    if api_key:
        embed = nextcord.Embed(
            title=f"📜 Case from {responsible_guild} [API_KEY]",
            color=nextcord.Color.orange()
        )
    else:
        embed = nextcord.Embed(
            title=f"📜 Case from {responsible_guild}",
            color=nextcord.Color.orange()
        )

    embed.add_field(
        name="🧑‍⚖️ Accused",
        value=accused if accused != "NaN" else "NaN",
        inline=False
    )
    embed.add_field(
        name="🔍 Investigator",
        value=investigator,
        inline=False
    )
    embed.add_field(
        name="⏳ Time",
        value=f"<t:{int(created_at)}:F>",
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

async def check_rate_limit(api_key: Optional[str]) -> bool:
    try:
        if not api_key:
            return True  # No API key provided, skip rate limit check

        key_info = database["keys"].find_one({"_id": api_key})
        if not key_info or "ratelimit" not in key_info:
            return True  # No rate limit set for this key, so no limit check

        rate_limit_info = key_info["ratelimit"]
        max_requests = rate_limit_info["max_requests"]
        time_window = rate_limit_info["time_window"]

        current_time = int(time.time())  # Current time in seconds
        last_request_time = rate_limit_info.get("last_request_time", current_time)
        request_count = rate_limit_info.get("request_count", 0)

        # Check if the time window has passed (current time - last request time > time window)
        if current_time - last_request_time >= time_window:
            request_count = 0

        if request_count >= max_requests:
            return False  # Rate limit exceeded, deny the request

        database["keys"].update_one(
            {"_id": api_key},
            {
                "$set": {
                    "ratelimit.last_request_time": current_time,  # Update last request time
                    "ratelimit.request_count": request_count + 1   # Increment request count
                }
            }
        )

        return True  # Allow the request
    except Exception as e:
        return False

async def authorize_action(master_password: str, api_key: Optional[str], action: str) -> bool:
    log.debug("Entering authorize_action")
    try:

        if master_password == system_config["api"]["master_password"]:
            return True

        if api_key:
            if not await check_rate_limit(api_key):
                return False

            key_info = database["keys"].find_one({"_id": api_key})
            if key_info and key_info.get(action, False):
                return True

        return False
    except Exception as e:
        log.error(f"Error in authorize_action: {e}", exc_info=True)
        return False

async def download_file(domain: str, path: str, dest: str):
    log.debug(f"Downloading file from {domain}{path}")
    try:
        if domain not in allowed_paths or not path.startswith(allowed_paths[domain]):
            logger.error(f"Invalid domain or path: {domain}{path}")
            return None

        url = f"https://{domain}{path}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    async with aiofiles.open(dest, 'wb') as f:
                        await f.write(await response.read())
                    return dest
                else:
                    logger.error(f"Failed to download file from {url} with status code {response.status}")
    except Exception as e:
        logger.error(f"Error downloading file {url}: {e}", exc_info=True)
    return None

@router.post("/create_case")
@limiter.limit("1/second")
async def create_case(request: Request, payload: CreateCase):
    if not await authorize_action(payload.master_password, payload.api_key, "create_case"):
        return {"code": 1, "body": "You are not authorized to run this action or you have exceeded the rate limit."}

    try:
        result = database["cases"].find_one({"accused": str(payload.accused_member)})
        if result:
            logger.warn("[CREATE_CASE] User already has a case against them, aborting..", debug=True)
            return {"code": 1, "body": f"This user already has a case against them: {result['_id']}", "case_id": result["_id"]}
    except Exception as e:
        logger.error(f"[CREATE_CASE] Failed during duplicate check: {e}")

    updated_proof_links = []

    try:
        # Ensure that 'temp_downloads' directory exists
        temp_downloads_dir = 'temp_downloads'
        if not os.path.exists(temp_downloads_dir):
            os.makedirs(temp_downloads_dir)  # Create directory if it doesn't exist

        with tempfile.TemporaryDirectory(prefix="proof_") as temp_dir:
            if system_config["api"]["proof_proxy"]:
                for link in payload.proof:
                    try:
                        if any(domain in link for domain in allowed_paths):
                            filename = os.path.basename(urlparse(link).path)
                            filepath = os.path.join(temp_downloads_dir, filename)  # Save to 'temp_downloads' directory

                            parsed_link = urlparse(link)
                            downloaded_file = await download_file(parsed_link.netloc, parsed_link.path, filepath)
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
                                    logger.error(f"[UPLOAD_ERROR] Failed to upload {filename}: {e}", exc_info=True)
                                finally:
                                    os.remove(downloaded_file)
                            else:
                                logger.error(f"Failed to download proof file: {link}")
                        else:
                            updated_proof_links.append(link)
                    except Exception as e:
                        logger.error(f"Error processing proof link {link}: {e}", exc_info=True)

        uuid = str(Generate.gen_id())

        database["cases"].insert_one({
            "_id": uuid,
            "server_id": str(payload.server_id),
            "accused": str(payload.accused_member),
            "investigator": str(payload.investigator_member),
            "reason": payload.reason.replace('',''),
            "created_at": int(datetime.datetime.now().timestamp()),
            "proof": updated_proof_links
        })

        if payload.api_key:
            embed = await build_case_embed(
                responsible_guild=str(payload.server_id),
                accused=str(payload.accused_member),
                investigator=str(payload.investigator_member),
                reason=f"{payload.reason.replace('`','')}",
                created_at=int(datetime.datetime.now().timestamp()),
                proof_links=updated_proof_links,
                api_key=True
            )
            embed.set_footer(text=f"Sent by {payload.api_key}")
        else:
            embed = await build_case_embed(
                responsible_guild=str(payload.server_id),
                accused=str(payload.accused_member),
                investigator=str(payload.investigator_member),
                reason=f"{payload.reason.replace('`','')}",
                created_at=int(datetime.datetime.now().timestamp()),
                proof_links=updated_proof_links
            )

        await webhook_logger.log_object(embed=embed)

    except Exception as f:
        logger.error(f"[CREATE_CASE] Database error: {f}")
        return {"code": 1, "body": "A database error has occurred."}

    return {
        "code": 0,
        "body": "Case created successfully.",
        "case_data": {"case_id": uuid, "time": int(datetime.datetime.now().timestamp())}
    }

@router.post("/delete_case")
@limiter.limit("1/second")
async def delete_case(request: Request, payload: DeleteCase):
    if system_config["api"].get("case_fetch_password_needed", False):
        if not await authorize_action(payload.master_password, payload.api_key, "delete_case"):
            return {"code": 1, "body": "You are not authorized to run this action."}
        
    await asyncio.sleep(1)  # dont ratelimit ourselves lol
    case_info = None

    try:
        async with httpx.AsyncClient() as client:
            case_info_response = await client.post(
                url=f"http://127.0.0.1:{system_config['api']['port']}/cases/fetch_case",
                json={
                    "master_password": system_config["api"]["master_password"],
                    "case_id": payload.case_id
                }
            )
            case_info_json = case_info_response.json()
            if case_info_json.get("code") == 0:
                case_info = case_info_json["case_data"]
    except Exception as e:
        logger.error(f"[DELETE_CASE] Failed to fetch case: {e}", exc_info=True)

    try:
        result = database["cases"].delete_one({"_id": payload.case_id})

        if result.deleted_count >= 1:

            if case_info:
                embed = await build_case_embed(
                    responsible_guild=case_info["server_id"],
                    accused=case_info["accused"],
                    investigator=case_info.get("investigator", "Unknown"),
                    created_at=case_info["created_at"],
                    reason=f"```{case_info["reason"].replace('`','')}```",
                    proof_links=case_info.get("proof", []),
                    api_key=bool(payload.api_key)
                )
                embed.title = f"🗑️ Case Deleted ({payload.case_id})"
                embed.color = nextcord.Color.red()
            else:
                embed = await build_case_embed(
                    responsible_guild=case_info["server_id"],
                    accused=case_info["accused"],
                    investigator=case_info.get("investigator", "Unknown"),
                    created_at=case_info["created_at"],
                    reason=f"```{case_info["reason"].replace('`','')}```",
                    proof_links=case_info.get("proof", []),
                    api_key=bool(payload.api_key)
                )
                embed.title = f"🗑️ Case Deleted ({payload.case_id})"
                embed.color = nextcord.Color.red()

            if payload.api_key and payload.api_key != "string":
                embed.add_field(name="🔑 API Key", value=f"`{payload.api_key}`", inline=False)

            await webhook_logger.log_object(embed=embed)

            return {"code": 0, "body": f"Case {payload.case_id} deleted successfully."}
        else:
            return {"code": 1, "body": "No case found with the provided case ID."}

    except Exception as e:
        logger.error(f"[DELETE_CASE] {e}", exc_info=True)
        return {"code": 1, "body": "A database error has occurred while deleting the case."}

@router.post("/fetch_case")
@limiter.limit("1/second")
async def fetch_case(request: Request, payload: FetchCase):
    log.debug("fetch_case endpoint called")
    if system_config["api"].get("case_fetch_password_needed", False):
        if not await authorize_action(payload.master_password, payload.api_key, "fetch_case"):
            return {"code": 1, "body": "You are not authorized to run this action."}
    try:
        case = database["cases"].find_one({"_id": payload.case_id})
        if not case:
            logger.warn("Case not found in fetch_case", debug=True)
            return {"code": 1, "body": "This case does not exist.", "found": False}

        case["_id"] = str(case["_id"])
        if system_config["api"].get("case_fetch_hide_investigator", False):
            if payload.master_password != system_config["api"]["master_password"]:
                case.pop("investigator", None)
        
        log.debug("fetch_case succeeded")
        return {"code": 0, "body": "This case exists, view the data.", "found": True, "case_data": case}
    except Exception as f:
        logger.error(f"[FETCH_CASE] {f}", exc_info=True)
        return {"code": 1, "found": False, "body": "A database error has occurred while finding a case."}

@router.post("/dump")
@limiter.limit("1/second")
async def dump(request: Request, payload: DumpCases):
    log.debug("dump endpoint called")
    if system_config["api"]["case_dump_password_needed"] != False:
        if not await authorize_action(payload.master_password, payload.api_key, "case_dump"):
            return {"code": 1, "body": "You are not authorized to run this action."}
        # if payload.master_password != system_config["api"]["master_password"]:
        #     return {"code": 1, "body": "You are not authorized to run this action."}
    try:
        cases_cursor = database["cases"].find()
        cases = []
        for case in cases_cursor:
            case["_id"] = str(case["_id"])
            if system_config["api"]["case_dump_hide_investigator"]:
                if payload.master_password != system_config["api"]["master_password"]:
                    case.pop("investigator", None)
            cases.append(case)
        log.debug("dump succeeded")
        return {"code": 0, "body": "All cases retrieved.", "cases": cases}
    except Exception as e:
        logger.error(f"[DUMP_CASES] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred while accessing the database.")
