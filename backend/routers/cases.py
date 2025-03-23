from fastapi import APIRouter
from pydantic import BaseModel, Field
from data import Data
import logger
import datetime
from utilities import Generate

database = Data.database

class CaseID(BaseModel):
    caseid: str

class CreateCase(BaseModel):
    accused_member: str
    investigator_member: str
    reason: str
    

router = APIRouter(prefix="/cases", tags=["cases"])

@router.post("/fetch_case")
async def fetch_case(request:CaseID):
    try:
        if not database["cases"].find_one({"caseid": request.caseid}):
            print("couldnt find a case")
        else:
            print("found a case")
    except Exception as f:
        logger.error(f"[FETCH_CASE] {f}")
        return {
            "code": 1,
            "body": "A database error has occured while finding a case."
            }


@router.post("/create_case")
async def create_case(request:CreateCase):
    uuid = Generate.gen_uuid()

    try:
        database["cases"].insert_one(
            {
                uuid: {
                    "accused": request.accused_member,
                    "investigator": request.investigator_member,
                    "reason": request.reason
                }
            }
        )
    except Exception as f:
        logger.error(f"[CREATE_CASE] {f}")
        return {
            "code": 1,
            "body": "A database error has occured."
            }
    
    return {
        "code": 0,
        "body": "Case created successfully.",
        "case_data": {
            "caseid": uuid or "NaN",
            "time": str(datetime.datetime.now())
        }
    }




    