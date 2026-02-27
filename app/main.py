from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.core.config import get_settings
from app.firebase_config import initialize_firebase

# Import routers from modules
from app.modules.hr.routes import router as hr_router
from app.modules.finance.routes import router as finance_router
from app.modules.logistics.router_logistica import router as logistics_router

# Initialize FastAPI application
app = FastAPI(
    title="RH_Agroserv ERP Backend",
    description="Backend for the Agroserv ERP project",
    version="0.1.0",
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Custom handler for validation errors.
    IMPORTANT: Includes CORS headers manually because regular exception handlers 
    bypass the CORSMiddleware.
    """
    errors = exc.errors()
    error_details = []
    has_missing_field = False
    
    first_error_field = "unknown"
    if errors:
        first_error_field = " -> ".join([str(loc) for loc in errors[0]["loc"]])

    for error in errors:
        field = " -> ".join([str(loc) for loc in error["loc"]])
        msg = f"{error['msg']} (type: {error['type']})"
        error_details.append({"field": field, "error": msg})
        if error["type"] == "missing":
            has_missing_field = True

    error_code = "LOG-ERR-MISSING-FIELD" if has_missing_field else "LOG-ERR-INVALID-FORMAT"
    
    # Get origin from request to mirror it in CORS (if allowed)
    origin = request.headers.get("origin")
    headers = {}
    if origin:
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "true"

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "code": error_code,
            "message": "Erro de validação: Verifique os nomes dos campos enviados no FormData.",
            "details": error_details,
            "required_fields_hint": ["arquivo_1", "arquivo_2 (optional)", "mapeamento"],
            "detected_error_location": first_error_field
        },
        headers=headers
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """
    Catch-all exception handler to ensure we return JSON and CORS headers even on 500 errors.
    """
    origin = request.headers.get("origin")
    headers = {}
    if origin:
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "true"

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "code": "INTERNAL_SERVER_ERROR",
            "message": f"Erro interno no servidor: {str(exc)}"
        },
        headers=headers
    )

# Initialize Firebase Admin SDK
initialize_firebase()

# Retrieve settings
settings = get_settings()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition", "X-Custom-Header"],
)

# Include modules' routers
app.include_router(hr_router, prefix="/api/hr", tags=["HR"])
app.include_router(finance_router, prefix="/api/finance", tags=["Finance"])
app.include_router(logistics_router, prefix="/api/logistica", tags=["Logistics"])

@app.get("/")
async def root():
    return {"message": "Welcome to RH_Agroserv ERP API", "status": "active"}

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
