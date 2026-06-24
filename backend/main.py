from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import analytics, security, system

app = FastAPI(
    title="LogLens API",
    description="Intelligent Web Log Analytics & Visualization Platform",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])
app.include_router(security.router, prefix="/api/v1/analytics/security", tags=["security"])
app.include_router(system.router, prefix="/api/v1/system", tags=["system"])

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
