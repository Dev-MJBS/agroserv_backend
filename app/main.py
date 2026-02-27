from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

# Initialize Firebase Admin SDK
initialize_firebase()

# Retrieve settings
settings = get_settings()

# CORS configuration
# Permitindo origens do Netlify e Localhost para desenvolvimento
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Para depuração inicial, use "*". Em produção, use sua lista de domínios.
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include modules' routers
app.include_router(hr_router, prefix="/api/hr", tags=["HR"])
app.include_router(finance_router, prefix="/api/finance", tags=["Finance"])
app.include_router(logistics_router, prefix="/logistica", tags=["Logistics"])

@app.get("/")
async def root():
    return {"message": "Welcome to RH_Agroserv ERP API", "status": "active"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
