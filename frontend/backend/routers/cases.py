import os
import time
import datetime
import logging
from urllib.parse import urlparse
from typing import List, Optional

import aiohttp
import aiofiles
from fastapi import APIRouter, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from data import Data
from modules import custom_uploads
from utilities import Generate, SystemConfig
import logger
from limiter import limiter  # limiter is defined inside `limiter.py`


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

async def check_rate_limit(api_key: Optional[str]) -> bool:
    log.debug("Entering check_rate_limit")
    try:
        if not api_key:
            return True

        key_info = database["keys"].find_one({"_id": api_key})
        if not key_info or "ratelimit" not in key_info:
            return True

        rate_limit_info = key_info["ratelimit"]
        max_requests = rate_limit_info["max_requests"]
        time_window = rate_limit_info["time_window"]

        current_time = int(time.time())
        last_request_time = rate_limit_info.get("last_request_time", current_time)
        request_count = rate_limit_info.get("request_count", 0)

        if current_time - last_request_time > time_window:
            request_count = 0

        if request_count >= max_requests:
            log.debug("Rate limit exceeded")
            return False

        database["keys"].update_one(
            {"_id": api_key},
            {"$set": {"ratelimit.last_request_time": current_time, "ratelimit.request_count": request_count + 1}}
        )

        log.debug("Exiting check_rate_limit with success")
        return True
    except Exception as e:
        log.error(f"Error in check_rate_limit: {e}", exc_info=True)
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

        log.debug("Exiting authorize_action with failure")
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
                    log.debug(f"File downloaded successfully: {dest}")
                    return dest
                else:
                    logger.error(f"Failed to download file from {url} with status code {response.status}")
    except Exception as e:
        logger.error(f"Error downloading file {url}: {e}", exc_info=True)
    return None

@router.post("/create_case")
@limiter.limit("1/second")
async def create_case(request: Request, payload: CreateCase):
    log.debug("create_case endpoint called")
    if not await authorize_action(payload.master_password, payload.api_key, "create_case"):
        return {"code": 1, "body": "You are not authorized to run this action or you have exceeded the rate limit."}

    try:
        result = database["cases"].find_one({"accused": str(payload.accused_member)})
        if result:
            logger.warn("[CREATE_CASE] User already has a case against them, aborting..", debug=True)
            return {"code": 1, "body": f"This user already has a case against them: {result['_id']}", "case_id": result["_id"]}
    except Exception as e:
        logger.error(f"[CREATE_CASE] Failed during duplicate check: {e}", exc_info=True)

    updated_proof_links = []
    temp_dir = "temp_downloads"
    os.makedirs(temp_dir, exist_ok=True)

    if system_config["api"]["proof_proxy"]:
        for link in payload.proof:
            try:
                if any(domain in link for domain in allowed_paths):
                    filename = os.path.basename(urlparse(link).path)
                    filepath = os.path.join(temp_dir, filename)

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

    try:
        database["cases"].insert_one({
            "_id": uuid,
            "server_id": str(payload.server_id),
            "accused": str(payload.accused_member),
            "investigator": str(payload.investigator_member),
            "reason": payload.reason,
            "created_at": int(datetime.datetime.now().timestamp()),
            "proof": updated_proof_links
        })
    except Exception as f:
        logger.error(f"[CREATE_CASE] Database error: {f}", exc_info=True)
        return {"code": 1, "body": "A database error has occurred."}

    log.debug("Exiting create_case successfully")
    return {
        "code": 0,
        "body": "Case created successfully.",
        "case_data": {"case_id": uuid, "time": int(datetime.datetime.now().timestamp())}
    }

@router.post("/delete_case")
@limiter.limit("1/second")
async def delete_case(request: Request, payload: DeleteCase):
    log.debug("delete_case endpoint called")
    if system_config["api"].get("case_fetch_password_needed", False):
        if not await authorize_action(payload.master_password, payload.api_key, "delete_case"):
            return {"code": 1, "body": "You are not authorized to run this action."}
    
    try:
        result = database["cases"].delete_one({"_id": payload.case_id})
        if result.deleted_count >= 1:
            log.debug("delete_case succeeded")
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
        if payload.master_password != system_config["api"]["master_password"]:
            return {"code": 1, "body": "You are not authorized to run this action."}
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
