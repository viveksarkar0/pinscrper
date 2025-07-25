#!/usr/bin/env python3
"""
Simple API runner for Pinterest Scraper
Run this to start the REST API server
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from fastapi import FastAPI, HTTPException, Depends, status
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel
    import uvicorn
    from dotenv import load_dotenv
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Please install: pip install fastapi uvicorn python-dotenv")
    sys.exit(1)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Pinterest Scraper API",
    description="REST API for Pinterest scraping with AI fashion analysis",
    version="1.0.0"
)

# Security
security = HTTPBearer()

def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify API key from Authorization header"""
    expected_key = os.getenv("API_KEY", "dev-api-key-12345")
    if credentials.credentials != expected_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return credentials.credentials

# Pydantic models
class HealthResponse(BaseModel):
    status: str
    message: str
    version: str

class ScrapeRequest(BaseModel):
    board_urls: list[str]
    max_pins: int = 50
    analyze_with_ai: bool = True

class JobResponse(BaseModel):
    job_id: str
    status: str
    message: str

# API Routes
@app.get("/", response_model=dict)
async def root():
    """Root endpoint"""
    return {
        "message": "Pinterest Scraper API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        message="Pinterest Scraper API is running",
        version="1.0.0"
    )

@app.post("/scrape", response_model=JobResponse)
async def start_scraping(
    request: ScrapeRequest,
    api_key: str = Depends(verify_api_key)
):
    """Start a new scraping job"""
    try:
        # For now, return a mock response
        # In production, this would start an actual scraping job
        job_id = f"job_{hash(str(request.board_urls))}"
        
        return JobResponse(
            job_id=job_id,
            status="started",
            message=f"Scraping job started for {len(request.board_urls)} boards"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start scraping job: {str(e)}"
        )

@app.get("/jobs/{job_id}")
async def get_job_status(
    job_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Get status of a scraping job"""
    # Mock response for now
    return {
        "job_id": job_id,
        "status": "completed",
        "progress": 100,
        "pins_scraped": 45,
        "message": "Job completed successfully"
    }

@app.get("/jobs")
async def list_jobs(
    api_key: str = Depends(verify_api_key),
    limit: int = 10,
    offset: int = 0
):
    """List all scraping jobs"""
    # Mock response for now
    return {
        "jobs": [
            {
                "job_id": "job_123",
                "status": "completed",
                "created_at": "2025-01-25T11:23:00Z",
                "pins_scraped": 45
            }
        ],
        "total": 1,
        "limit": limit,
        "offset": offset
    }

@app.get("/pins")
async def list_pins(
    api_key: str = Depends(verify_api_key),
    limit: int = 20,
    offset: int = 0,
    job_id: str = None
):
    """List scraped pins"""
    # Mock response for now
    return {
        "pins": [
            {
                "pin_id": "pin_123",
                "url": "https://pinterest.com/pin/123",
                "image_url": "https://example.com/image.jpg",
                "title": "Fashion Item",
                "description": "Beautiful fashion piece",
                "board_name": "Fashion Board",
                "scraped_at": "2025-01-25T11:23:00Z"
            }
        ],
        "total": 1,
        "limit": limit,
        "offset": offset
    }

if __name__ == "__main__":
    # Configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "true").lower() == "true"
    
    print(f"🚀 Starting Pinterest Scraper API")
    print(f"📍 Server: http://{host}:{port}")
    print(f"📚 Documentation: http://{host}:{port}/docs")
    print(f"🔑 API Key: {os.getenv('API_KEY', 'dev-api-key-12345')}")
    print(f"🐛 Debug Mode: {debug}")
    
    # Start the server
    uvicorn.run(
        "run_api:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info" if debug else "warning"
    )
