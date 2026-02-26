from fastapi import APIRouter

router = APIRouter()

@router.get("/status")
async def finance_status():
    """
    Endpoint for testing Finance module status.
    """
    return {"module": "Finance", "status": "online"}
