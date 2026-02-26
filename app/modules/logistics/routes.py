from fastapi import APIRouter

router = APIRouter()

@router.get("/status")
async def logistics_status():
    """
    Endpoint for testing Logistics module status.
    """
    return {"module": "Logistics", "status": "online"}
