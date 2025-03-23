from fastapi import APIRouter
from pydantic import BaseModel, Field
from data import Data
import logger
import datetime
from utilities import Generate, SystemConfig

system_config = SystemConfig.system_config
database = Data.database

class CaseID(BaseModel):
    caseid: str

class CreateCase(BaseModel):
    master_password: str = Field(min_length=12, max_length=999999999999999)
    accused_member: str
    investigator_member: str
    reason: str

class DeleteCase(BaseModel):
    master_password: str = Field(min_length=12, max_length=999999999999999)
    caseid: str

router = APIRouter(prefix="/cases", tags=["cases"])

@router.post("/delete_case")
async def delete_case(request: DeleteCase):
    if request.master_password != system_config["api"]["master_password"]:
        return {
            "code": 1,
            "body": "You are not authorized to run this action."
        }
    
    try:
        result = database["cases"].delete_one({"_id": request.caseid})

        if result.deleted_count >= 1:
            return {
                "code": 0,
                "body": f"Case {request.caseid} deleted successfully."
            }
        else:
            return {
                "code": 1,
                "body": "No case found with the provided case ID."
            }

    except Exception as e:
        logger.error(f"[DELETE_CASE] {e}")
        return {
            "code": 1,
            "body": "A database error has occurred while deleting the case."
        }


@router.post("/fetch_case")
async def fetch_case(request: CaseID):
    try:
        case = database["cases"].find_one({"_id": request.caseid})
        if not case:
            logger.warn("Received request from /fetch_case, case doesn't exist", debug=True)
            return {
                "code": 1,
                "body": "This case does not exist.",
                "found": False
            }

        return {
            "code": 0,
            "body": "This case exists, view the data.",
            "found": True,
            "case_data": case
        }
    except Exception as f:
        logger.error(f"[FETCH_CASE] {f}")
        return {
            "code": 1,
            "found": False,
            "body": "A database error has occurred while finding a case."
        }



@router.post("/create_case")
async def create_case(request: CreateCase):
    if request.master_password != system_config["api"]["master_password"]:
        return {
            "code": 1,
            "body": "You are not authorized to run this action."
        }

    uuid = str(Generate.gen_id())

    try:
        database["cases"].insert_one({
            "_id": uuid,
            "accused": request.accused_member,
            "investigator": request.investigator_member,
            "reason": request.reason,
            "created_at": int(datetime.datetime.now().timestamp())
        })

    except Exception as f:
        logger.error(f"[CREATE_CASE] {f}")
        return {
            "code": 1,
            "body": "A database error has occurred."
        }

    return {
        "code": 0,
        "body": "Case created successfully.",
        "case_data": {
            "caseid": uuid,
            "time": int(datetime.datetime.now().timestamp())
        }
    }


    