#!/usr/bin/env python3
"""
Pinterest Scraper REST API
FastAPI-based REST API for Pinterest scraping with MongoDB storage
AWS deployment ready
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import asyncio
import logging
from datetime import datetime
import os
from contextlib import asynccontextmanager

# Local imports
from .database import MongoDB
from .models import (
    ScrapingJobRequest, ScrapingJobResponse, PinResponse, 
    JobStatus, AnalysisRequest, AnalysisResponse
)
from .scraper_service import ScraperService
from .auth import verify_api_key
from .config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
mongodb: MongoDB = None
scraper_service: ScraperService = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global mongodb, scraper_service
    
    # Startup
    settings = get_settings()
    mongodb = MongoDB(settings.mongodb_url, settings.database_name)
    await mongodb.connect()
    
    scraper_service = ScraperService(mongodb, settings)
    
    logger.info("Pinterest Scraper API started successfully")
    
    yield
    
    # Shutdown
    await mongodb.disconnect()
    logger.info("Pinterest Scraper API shutdown complete")

# Initialize FastAPI app
app = FastAPI(
    title="Pinterest Scraper API",
    description="Production-level Pinterest scraper with AI fashion analysis",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Pinterest Scraper API",
        "version": "1.0.0",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        # Check database connection
        db_status = await mongodb.health_check()
        
        return {
            "status": "healthy",
            "database": "connected" if db_status else "disconnected",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "scraper": "available",
                "ai_analyzer": "available",
                "database": "connected" if db_status else "error"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

@app.post("/scrape", response_model=ScrapingJobResponse)
async def start_scraping_job(
    request: ScrapingJobRequest,
    background_tasks: BackgroundTasks,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Start a new scraping job"""
    # Verify API key
    await verify_api_key(credentials.credentials)
    
    try:
        # Create job in database
        job_id = await scraper_service.create_scraping_job(request)
        
        # Start scraping in background
        background_tasks.add_task(
            scraper_service.execute_scraping_job,
            job_id,
            request
        )
        
        return ScrapingJobResponse(
            job_id=job_id,
            status=JobStatus.PENDING,
            message="Scraping job started successfully",
            created_at=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Failed to start scraping job: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start scraping job: {str(e)}"
        )

@app.get("/jobs/{job_id}", response_model=ScrapingJobResponse)
async def get_job_status(
    job_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get status of a scraping job"""
    await verify_api_key(credentials.credentials)
    
    try:
        job = await scraper_service.get_job_status(job_id)
        if not job:
            raise HTTPException(
                status_code=404,
                detail="Job not found"
            )
        
        return job
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get job status: {str(e)}"
        )

@app.get("/jobs", response_model=List[ScrapingJobResponse])
async def list_jobs(
    skip: int = 0,
    limit: int = 10,
    status: Optional[JobStatus] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """List scraping jobs with pagination"""
    await verify_api_key(credentials.credentials)
    
    try:
        jobs = await scraper_service.list_jobs(skip, limit, status)
        return jobs
        
    except Exception as e:
        logger.error(f"Failed to list jobs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list jobs: {str(e)}"
        )

@app.get("/jobs/{job_id}/pins", response_model=List[PinResponse])
async def get_job_pins(
    job_id: str,
    skip: int = 0,
    limit: int = 50,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get pins from a completed scraping job"""
    await verify_api_key(credentials.credentials)
    
    try:
        pins = await scraper_service.get_job_pins(job_id, skip, limit)
        return pins
        
    except Exception as e:
        logger.error(f"Failed to get job pins: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get job pins: {str(e)}"
        )

@app.get("/pins", response_model=List[PinResponse])
async def search_pins(
    query: Optional[str] = None,
    tags: Optional[List[str]] = None,
    board_name: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Search pins with filters"""
    await verify_api_key(credentials.credentials)
    
    try:
        filters = {}
        if query:
            filters['query'] = query
        if tags:
            filters['tags'] = tags
        if board_name:
            filters['board_name'] = board_name
            
        pins = await scraper_service.search_pins(filters, skip, limit)
        return pins
        
    except Exception as e:
        logger.error(f"Failed to search pins: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search pins: {str(e)}"
        )

@app.get("/pins/{pin_id}", response_model=PinResponse)
async def get_pin(
    pin_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get a specific pin by ID"""
    await verify_api_key(credentials.credentials)
    
    try:
        pin = await scraper_service.get_pin(pin_id)
        if not pin:
            raise HTTPException(
                status_code=404,
                detail="Pin not found"
            )
        
        return pin
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get pin: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get pin: {str(e)}"
        )

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_image(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Analyze an image with AI fashion analysis"""
    await verify_api_key(credentials.credentials)
    
    try:
        # Start analysis in background if requested
        if request.async_analysis:
            analysis_id = await scraper_service.create_analysis_job(request)
            background_tasks.add_task(
                scraper_service.execute_analysis_job,
                analysis_id,
                request
            )
            
            return AnalysisResponse(
                analysis_id=analysis_id,
                status="pending",
                message="Analysis job started"
            )
        else:
            # Synchronous analysis
            result = await scraper_service.analyze_image_sync(request)
            return result
            
    except Exception as e:
        logger.error(f"Failed to analyze image: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze image: {str(e)}"
        )

@app.get("/analysis/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis_result(
    analysis_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get analysis result by ID"""
    await verify_api_key(credentials.credentials)
    
    try:
        result = await scraper_service.get_analysis_result(analysis_id)
        if not result:
            raise HTTPException(
                status_code=404,
                detail="Analysis not found"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get analysis result: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get analysis result: {str(e)}"
        )

@app.get("/stats")
async def get_statistics(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get scraping statistics"""
    await verify_api_key(credentials.credentials)
    
    try:
        stats = await scraper_service.get_statistics()
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get statistics: {str(e)}"
        )

@app.delete("/jobs/{job_id}")
async def delete_job(
    job_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Delete a scraping job and its data"""
    await verify_api_key(credentials.credentials)
    
    try:
        success = await scraper_service.delete_job(job_id)
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Job not found"
            )
        
        return {"message": "Job deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete job: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete job: {str(e)}"
        )

@app.get("/export/{job_id}")
async def export_training_dataset(
    job_id: str,
    format: str = "json",
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Export training dataset in various formats"""
    await verify_api_key(credentials.credentials)
    
    try:
        if format not in ["json", "csv", "parquet"]:
            raise HTTPException(
                status_code=400,
                detail="Unsupported format. Use: json, csv, or parquet"
            )
        
        dataset = await scraper_service.export_training_dataset(job_id, format)
        
        return {
            "job_id": job_id,
            "format": format,
            "dataset": dataset,
            "exported_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export dataset: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to export dataset: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
