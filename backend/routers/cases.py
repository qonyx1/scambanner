import aiohttp
import aiofiles
import os
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List, Optional
from data import Data
from urllib.parse import urlparse
import logger
import datetime
from modules import custom_uploads
from utilities import Generate, SystemConfig

system_config = SystemConfig.system_config
database = Data.database


class case_id(BaseModel):
    case_id: str

class FetchCase(BaseModel):
    master_password: str
    case_id: str
    api_key: Optional[str] = None

class CreateCase(BaseModel):
    master_password: str
    server_id: int
    accused_member: int
    investigator_member: int
    reason: str
    proof: List[str] = []
    api_key: Optional[str] = None

class DumpCases(BaseModel):
    master_password: str
    api_key: Optional[str] = None

class DeleteCase(BaseModel):
    master_password: str
    case_id: str

allowed_paths = {
    "cdn.discordapp.com": "/attachments/",
    "media.discordapp.net": "/attachments/",
    "images-ext-1.discordapp.net": "/external/"
}

router = APIRouter(prefix="/cases", tags=["cases"])

def authorize_action(master_password: str, api_key: Optional[str], action: str) -> bool:
    if master_password == system_config["api"]["master_password"]:
        return True

    if api_key:
        key_info = database["keys"].find_one({"key": api_key})
        if key_info and key_info.get(action, False):
            return True

    return False

async def download_file(domain: str, path: str, dest: str):
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
        logger.error(f"Error downloading file {url}: {e}")
    return None

@router.post("/create_case")
async def create_case(request: CreateCase):
    if not authorize_action(request.master_password, request.api_key, "create_case"):
        return {"code": 1, "body": "You are not authorized to run this action."}
    
    try: # users cant have duplicate cases
        result = database["cases"].find_one({"accused": str(request.accused_member)})
        if result:
            logger.warn("[CREATE_CASE] User already has a case against them, aborting..", debug=True)
            return {"code": 1, "body": f"This user already has a case against them: {result["_id"]}", "case_id": result["_id"]}
        
        
    except:
        logger.error(f"[CREATE_CASE] Failed to check if the user has a case against them (line 64).")

    updated_proof_links = []
    temp_dir = "temp_downloads"
    os.makedirs(temp_dir, exist_ok=True)


    if system_config["api"]["proof_proxy"]:
        for link in request.proof:
            if any(domain in link for domain in discord_cdn_domains):
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
                        logger.error(f"[UPLOAD_ERROR] Failed to upload {filename}: {e}")
                    finally:
                        os.remove(downloaded_file)
                else:
                    logger.error(f"Failed to download proof file: {link}")
            else:
                updated_proof_links.append(link)

    uuid = str(Generate.gen_id())

    try:
        database["cases"].insert_one({
            "_id": uuid,
            "server_id": str(request.server_id),
            "accused": str(request.accused_member),
            "investigator": str(request.investigator_member),
            "reason": request.reason,
            "created_at": int(datetime.datetime.now().timestamp()),
            "proof": updated_proof_links
        })
    except Exception as f:
        logger.error(f"[CREATE_CASE] {f}")
        return {"code": 1, "body": "A database error has occurred."}

    return {
        "code": 0,
        "body": "Case created successfully.",
        "case_data": {"case_id": uuid, "time": int(datetime.datetime.now().timestamp())}
    }

@router.post("/delete_case")
async def delete_case(request: DeleteCase):
    if system_config["api"].get("case_fetch_password_needed", False):
        if not authorize_action(request.master_password, request.api_key, "delete_case"):
            return {"code": 1, "body": "You are not authorized to run this action."}
    
    try:
        result = database["cases"].delete_one({"_id": request.case_id})

        if result.deleted_count >= 1:
            return {"code": 0, "body": f"Case {request.case_id} deleted successfully."}
        else:
            return {"code": 1, "body": "No case found with the provided case ID."}
    except Exception as e:
        logger.error(f"[DELETE_CASE] {e}")
        return {"code": 1, "body": "A database error has occurred while deleting the case."}

@router.post("/fetch_case")
async def fetch_case(request: FetchCase):
    if system_config["api"].get("case_fetch_password_needed", False):
        if not authorize_action(request.master_password, request.api_key, "fetch_case"):
            return {"code": 1, "body": "You are not authorized to run this action."}
    try:
        case = database["cases"].find_one({"_id": request.case_id})
        if not case:
            logger.warn("Received request from /fetch_case, case doesn't exist", debug=True)
            return {"code": 1, "body": "This case does not exist.", "found": False}
        
        case["_id"] = str(case["_id"])
        if system_config["api"].get("case_fetch_hide_investigator", False):
            if request.master_password != system_config["api"]["master_password"]:
                case.pop("investigator", None)
        
        return {"code": 0, "body": "This case exists, view the data.", "found": True, "case_data": case}
    except Exception as f:
        logger.error(f"[FETCH_CASE] {f}")
        return {"code": 1, "found": False, "body": "A database error has occurred while finding a case."}

@router.post("/dump")
async def dump(request: DumpCases):
    if system_config["api"]["case_dump_password_needed"] != False:
        if request.master_password != system_config["api"]["master_password"]:
            return {"code": 1, "body": "You are not authorized to run this action."}
    try:
        cases_cursor = database["cases"].find()
        cases = []
        for case in cases_cursor:
            case["_id"] = str(case["_id"])

            if system_config["api"]["case_dump_hide_investigator"]:
                if request.master_password != system_config["api"]["master_password"]:
                    case.pop("investigator", None)

            cases.append(case)
        
        return {"code": 0, "body": "All cases retrieved.", "cases": cases}
    except Exception as e:
        logger.error(f"[DUMP_CASES] {e}")
        raise {"code": 1, "body": "An error occured while accessing the database."}