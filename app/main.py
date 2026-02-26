from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.firebase_config import initialize_firebase

# Import routers from modules
from app.modules.hr.routes import router as hr_router
from app.modules.finance.routes import router as finance_router
from app.modules.logistics.routes import router as logistics_router

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
# Prepared for Next.js frontend on Netlify or local environment
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include modules' routers
app.include_router(hr_router, prefix="/api/hr", tags=["HR"])
app.include_router(finance_router, prefix="/api/finance", tags=["Finance"])
app.include_router(logistics_router, prefix="/api/logistics", tags=["Logistics"])

@app.get("/")
async def root():
    return {"message": "Welcome to RH_Agroserv ERP API", "status": "active"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
