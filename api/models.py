#!/usr/bin/env python3
"""
Pydantic models for Pinterest Scraper API
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum

class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ScrapingJobRequest(BaseModel):
    """Request model for starting a scraping job"""
    board_urls: List[HttpUrl] = Field(..., description="List of Pinterest board URLs to scrape")
    max_pins_per_board: Optional[int] = Field(100, description="Maximum pins to scrape per board")
    enable_ai_analysis: Optional[bool] = Field(True, description="Enable AI fashion analysis")
    job_name: Optional[str] = Field(None, description="Optional name for the job")
    tags: Optional[List[str]] = Field([], description="Tags to associate with this job")
    
    class Config:
        schema_extra = {
            "example": {
                "board_urls": [
                    "https://in.pinterest.com/mohanty2922/y2k-fashion/",
                    "https://in.pinterest.com/mohanty2922/office/"
                ],
                "max_pins_per_board": 50,
                "enable_ai_analysis": True,
                "job_name": "Fashion Dataset Collection",
                "tags": ["fashion", "y2k", "office-wear"]
            }
        }

class ScrapingJobResponse(BaseModel):
    """Response model for scraping job status"""
    job_id: str
    status: JobStatus
    message: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    job_name: Optional[str] = None
    board_urls: Optional[List[str]] = None
    total_pins_scraped: Optional[int] = 0
    total_pins_analyzed: Optional[int] = 0
    error_message: Optional[str] = None
    progress_percentage: Optional[float] = 0.0
    tags: Optional[List[str]] = []

class FashionItem(BaseModel):
    """Fashion item detected by AI"""
    category: str
    type: str
    color: List[str]
    material: str
    style: str
    brand: str
    confidence: Optional[float] = None
    fabric_details: Optional[List[Dict[str, str]]] = []
    specific_type: Optional[str] = None
    additional_attributes: Optional[Dict[str, Any]] = {}
    season_appropriateness: Optional[List[str]] = []
    occasion_suitability: Optional[List[str]] = []
    price_range_estimate: Optional[str] = None
    trend_status: Optional[str] = None

class AIAnalysis(BaseModel):
    """AI analysis result for a pin"""
    fashion_items: List[FashionItem] = []
    overall_outfit_analysis: Optional[Dict[str, Any]] = {}
    style_analysis: Optional[Dict[str, Any]] = {}
    analysis_timestamp: datetime
    confidence_score: Optional[float] = None

class PinResponse(BaseModel):
    """Response model for Pinterest pin data"""
    pin_id: str
    title: str
    description: str
    image_url: HttpUrl
    local_image_path: Optional[str] = None
    board_name: str
    board_url: HttpUrl
    author: str
    save_count: Optional[int] = None
    created_date: Optional[datetime] = None
    scraped_at: datetime
    job_id: str
    ai_analysis: Optional[AIAnalysis] = None
    tags: List[str] = []
    
    class Config:
        schema_extra = {
            "example": {
                "pin_id": "1012887772451572733",
                "title": "Y2K Fashion Outfit",
                "description": "Trendy Y2K style outfit perfect for summer",
                "image_url": "https://i.pinimg.com/736x/example.jpg",
                "local_image_path": "/images/1012887772451572733.jpg",
                "board_name": "y2k-fashion",
                "board_url": "https://in.pinterest.com/mohanty2922/y2k-fashion/",
                "author": "mohanty2922",
                "scraped_at": "2025-07-25T11:07:09.153202",
                "job_id": "job_123456",
                "tags": ["y2k", "fashion", "summer", "trendy"]
            }
        }

class AnalysisRequest(BaseModel):
    """Request model for image analysis"""
    image_url: Optional[HttpUrl] = None
    image_base64: Optional[str] = None
    analysis_type: Optional[str] = Field("comprehensive", description="Type of analysis: basic, comprehensive, or advanced")
    async_analysis: Optional[bool] = Field(False, description="Run analysis asynchronously")
    
    class Config:
        schema_extra = {
            "example": {
                "image_url": "https://example.com/fashion-image.jpg",
                "analysis_type": "comprehensive",
                "async_analysis": False
            }
        }

class AnalysisResponse(BaseModel):
    """Response model for image analysis"""
    analysis_id: str
    status: str
    message: Optional[str] = None
    ai_analysis: Optional[AIAnalysis] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

class SearchFilters(BaseModel):
    """Search filters for pins"""
    query: Optional[str] = None
    tags: Optional[List[str]] = None
    board_name: Optional[str] = None
    author: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    has_ai_analysis: Optional[bool] = None
    fashion_categories: Optional[List[str]] = None
    colors: Optional[List[str]] = None
    styles: Optional[List[str]] = None

class TrainingDatasetRequest(BaseModel):
    """Request model for generating training dataset"""
    job_ids: Optional[List[str]] = None
    filters: Optional[SearchFilters] = None
    format: Optional[str] = Field("json", description="Export format: json, csv, or parquet")
    include_images: Optional[bool] = Field(True, description="Include image data in export")
    
class TrainingDatasetResponse(BaseModel):
    """Response model for training dataset"""
    dataset_id: str
    total_samples: int
    format: str
    download_url: Optional[str] = None
    metadata: Dict[str, Any]
    created_at: datetime
    expires_at: Optional[datetime] = None

class Statistics(BaseModel):
    """API statistics"""
    total_jobs: int
    total_pins_scraped: int
    total_pins_analyzed: int
    total_images_downloaded: int
    jobs_by_status: Dict[str, int]
    top_boards: List[Dict[str, Any]]
    top_tags: List[Dict[str, Any]]
    analysis_stats: Dict[str, Any]
    storage_stats: Dict[str, Any]

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: str
    timestamp: datetime
    request_id: Optional[str] = None

# MongoDB Document Models (for internal use)
class JobDocument(BaseModel):
    """MongoDB document for scraping jobs"""
    job_id: str
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    job_name: Optional[str] = None
    board_urls: List[str]
    max_pins_per_board: int
    enable_ai_analysis: bool
    total_pins_scraped: int = 0
    total_pins_analyzed: int = 0
    error_message: Optional[str] = None
    progress_percentage: float = 0.0
    tags: List[str] = []
    config: Dict[str, Any] = {}

class PinDocument(BaseModel):
    """MongoDB document for pins"""
    pin_id: str
    title: str
    description: str
    image_url: str
    local_image_path: Optional[str] = None
    board_name: str
    board_url: str
    author: str
    save_count: Optional[int] = None
    created_date: Optional[datetime] = None
    scraped_at: datetime
    job_id: str
    ai_analysis: Optional[Dict[str, Any]] = None
    tags: List[str] = []
    image_hash: Optional[str] = None
    file_size: Optional[int] = None
    image_dimensions: Optional[Dict[str, int]] = None

class AnalysisDocument(BaseModel):
    """MongoDB document for analysis jobs"""
    analysis_id: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    image_url: Optional[str] = None
    image_base64: Optional[str] = None
    analysis_type: str
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
