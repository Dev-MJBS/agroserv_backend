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
    Custom handler for validation errors (like "Field required").
    Returns a specific code and clear message to help the frontend developer.
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

    # Code generation as requested: LOG-REQ (Required field missing) or LOG-VAL (Invalid data)
    error_code = "LOG-ERR-MISSING-FIELD" if has_missing_field else "LOG-ERR-INVALID-FORMAT"
    
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
    )

# Initialize Firebase Admin SDK
initialize_firebase()

# Retrieve settings
settings = get_settings()

# CORS configuration
# Se allow_credentials=True, allow_origins NÃO pode ser ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://agroserv.netlify.app",
        "http://localhost:3000",
        "https://agroserv-git-main-dev-mjbs.vercel.app" # Exemplo de preview
    ],
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
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
