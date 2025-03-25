import aiohttp
import aiofiles
import os
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List
from data import Data
from urllib.parse import urlparse
import logger
import datetime
from modules import custom_uploads
from utilities import Generate, SystemConfig

system_config = SystemConfig.system_config
database = Data.database

discord_cdn_domains = [
    "cdn.discordapp.com", 
    "media.discordapp.net",
    "images-ext-1.discordapp.net"
]

class CaseID(BaseModel):
    caseid: str

class CreateCase(BaseModel):
    master_password: str = Field(min_length=12, max_length=999999999999999)
    server_id: int
    accused_member: int
    investigator_member: int
    reason: str
    proof: List[str] = []

class DeleteCase(BaseModel):
    master_password: str = Field(min_length=12, max_length=999999999999999)
    caseid: str

router = APIRouter(prefix="/cases", tags=["cases"])

async def download_file(url: str, dest: str):
    try:
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
    if request.master_password != system_config["api"]["master_password"]:
        return {"code": 1, "body": "You are not authorized to run this action."}

    updated_proof_links = []
    temp_dir = "temp_downloads"
    os.makedirs(temp_dir, exist_ok=True)

    if system_config["api"]["proof_proxy"]:
        for link in request.proof:
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
        "case_data": {"caseid": uuid, "time": int(datetime.datetime.now().timestamp())}
    }

@router.post("/delete_case")
async def delete_case(request: DeleteCase):
    if request.master_password != system_config["api"]["master_password"]:
        return {"code": 1, "body": "You are not authorized to run this action."}
    
    try:
        result = database["cases"].delete_one({"_id": request.caseid})

        if result.deleted_count >= 1:
            return {"code": 0, "body": f"Case {request.caseid} deleted successfully."}
        else:
            return {"code": 1, "body": "No case found with the provided case ID."}
    except Exception as e:
        logger.error(f"[DELETE_CASE] {e}")
        return {"code": 1, "body": "A database error has occurred while deleting the case."}

@router.post("/fetch_case")
async def fetch_case(request: CaseID):
    try:
        case = database["cases"].find_one({"_id": request.caseid})
        if not case:
            logger.warn("Received request from /fetch_case, case doesn't exist", debug=True)
            return {"code": 1, "body": "This case does not exist.", "found": False}
        return {"code": 0, "body": "This case exists, view the data.", "found": True, "case_data": case}
    except Exception as f:
        logger.error(f"[FETCH_CASE] {f}")
        return {"code": 1, "found": False, "body": "A database error has occurred while finding a case."}
