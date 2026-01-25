from fastapi import FastAPI
from app.routers import example

app = FastAPI(
    title="FastAPI to CDK Gateway",
    description="FastAPI application that can be translated to AWS CDK API Gateway",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Include routers
app.include_router(example.router, prefix="/api/v1", tags=["todos"])


@app.get("/", tags=["health"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "FastAPI to CDK Gateway - API is running",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
