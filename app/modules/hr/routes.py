from fastapi import APIRouter
from typing import List, Dict

router = APIRouter()

@router.get("/status")
async def hr_status():
    """
    Endpoint for testing HR module status.
    Returns a simple JSON status object.
    """
    return {
        "module": "Human Resources",
        "status": "online",
        "endpoints": [
            "/status",
            "/employees (placeholder)"
        ]
    }

@router.get("/employees")
async def get_test_employees():
    """
    Temporary endpoint returning test employees.
    """
    return [
        {"id": 1, "name": "João Silva", "role": "Supervisor de Campo"},
        {"id": 2, "name": "Maria Fernandes", "role": "Engenheira Agrônoma"}
    ]
