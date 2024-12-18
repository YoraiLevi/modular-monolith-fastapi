from fastapi import APIRouter
from common.logging.getLogger import getContextualLogger

router = APIRouter()


# keep as empty path? https://github.com/fastapi/fastapi/issues/2060#issuecomment-1158967722
@router.get("")
async def root():
    getContextualLogger().info("Status OK")
    return {"status": "OK"}
