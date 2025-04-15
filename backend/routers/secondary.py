from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel
from data import Data
import logger
from limiter import limiter
import os

database = Data.database

router = APIRouter(prefix="/legal", tags=["legal"])

@router.get("/privacy-policy")
@limiter.limit("8/minute")
async def get_privacy_policy(request: Request):
    file_path = "./resources/PrivacyPolicy.pdf"
    if os.path.exists(file_path):
        return FileResponse(path=file_path, filename="PrivacyPolicy.pdf", media_type="application/pdf")
    else:
        raise HTTPException(status_code=404, detail="Privacy policy not found")
