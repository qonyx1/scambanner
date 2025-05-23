from fastapi import APIRouter
from pydantic import BaseModel
from data import Data
import logger
from limiter import limiter
from fastapi import APIRouter, HTTPException, Request

database = Data.database

router = APIRouter(prefix="/checks", tags=["checks"])

class CheckID(BaseModel):
    accused_member: int

@router.post("/check_id")
@limiter.limit("1/second")
async def check_id(request: Request, payload: CheckID):
    try:
        result = database["cases"].find_one({"accused": str(payload.accused_member)})

        if result:
            return {
                "code": 0,
                "case_id": result["_id"]
            }
        else:
            return {
                "code": 1,
                "body": "No case found for this member."
            }

    except Exception as e:
        logger.error(f"[CHECK_ID] {e}")
        return {
            "code": 1,
            "body": "A database error has occurred."
        }
