#!/usr/bin/env python3
"""
Scraper Service for Pinterest API
Handles scraping operations and AI analysis
"""

import asyncio
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Any
import logging
import json
import os
from pathlib import Path

from .database import MongoDB
from .models import (
    ScrapingJobRequest, ScrapingJobResponse, PinResponse, 
    JobStatus, AnalysisRequest, AnalysisResponse, JobDocument, 
    PinDocument, AnalysisDocument, AIAnalysis, FashionItem
)
from ..pinterest_scraper import PinterestScraper, PinData
from ..ai_fashion_analyzer import AIFashionAnalyzer

logger = logging.getLogger(__name__)

class ScraperService:
    """Service layer for Pinterest scraping operations"""
    
    def __init__(self, mongodb: MongoDB, settings):
        self.mongodb = mongodb
        self.settings = settings
        self.ai_analyzer = None
        
        # Initialize AI analyzer if API key is available
        if settings.gemini_api_key and settings.gemini_api_key != "YOUR_GEMINI_API_KEY_HERE":
            try:
                self.ai_analyzer = AIFashionAnalyzer(settings.gemini_api_key)
                logger.info("AI Fashion Analyzer initialized")
            except Exception as e:
                logger.error(f"Failed to initialize AI analyzer: {e}")
    
    async def create_scraping_job(self, request: ScrapingJobRequest) -> str:
        """Create a new scraping job"""
        job_id = str(uuid.uuid4())
        
        job_data = JobDocument(
            job_id=job_id,
            status=JobStatus.PENDING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            job_name=request.job_name,
            board_urls=[str(url) for url in request.board_urls],
            max_pins_per_board=request.max_pins_per_board,
            enable_ai_analysis=request.enable_ai_analysis,
            tags=request.tags or [],
            config={
                "pinterest_email": self.settings.pinterest_email,
                "pinterest_password": self.settings.pinterest_password,
                "gemini_api_key": self.settings.gemini_api_key,
                "headless": True,  # Always headless for API
                "request_delay": 2,
                "max_workers": 3
            }
        )
        
        await self.mongodb.create_job(job_data)
        logger.info(f"Created scraping job: {job_id}")
        
        return job_id
    
    async def execute_scraping_job(self, job_id: str, request: ScrapingJobRequest):
        """Execute scraping job in background"""
        try:
            # Update job status to running
            await self.mongodb.update_job(job_id, {
                "status": JobStatus.RUNNING.value,
                "progress_percentage": 0.0
            })
            
            # Initialize scraper with job-specific config
            scraper_config = {
                "output_dir": f"scraped_data/{job_id}",
                "images_dir": "images",
                "max_pins_per_board": request.max_pins_per_board,
                "headless": True,
                "pinterest_email": self.settings.pinterest_email,
                "pinterest_password": self.settings.pinterest_password,
                "gemini_api_key": self.settings.gemini_api_key if request.enable_ai_analysis else "",
                "request_delay": 2,
                "max_workers": 3
            }
            
            # Create temporary config file for this job
            config_path = f"/tmp/config_{job_id}.json"
            with open(config_path, 'w') as f:
                json.dump(scraper_config, f)
            
            # Initialize scraper
            scraper = PinterestScraper(config_path)
            
            # Convert URLs to strings
            board_urls = [str(url) for url in request.board_urls]
            
            # Execute scraping
            scraped_pins = scraper.scrape_boards(board_urls)
            
            # Process and store pins in database
            total_pins = len(scraped_pins)
            processed_pins = 0
            
            for pin in scraped_pins:
                try:
                    # Convert PinData to PinDocument
                    pin_doc = await self._convert_pin_to_document(pin, job_id)
                    await self.mongodb.create_pin(pin_doc)
                    
                    processed_pins += 1
                    progress = (processed_pins / total_pins) * 100
                    
                    # Update progress
                    await self.mongodb.update_job(job_id, {
                        "progress_percentage": progress,
                        "total_pins_scraped": processed_pins
                    })
                    
                except Exception as e:
                    logger.error(f"Failed to store pin {pin.pin_id}: {e}")
                    continue
            
            # Count analyzed pins
            analyzed_count = len([p for p in scraped_pins if p.ai_analysis])
            
            # Mark job as completed
            await self.mongodb.update_job(job_id, {
                "status": JobStatus.COMPLETED.value,
                "completed_at": datetime.utcnow(),
                "progress_percentage": 100.0,
                "total_pins_scraped": processed_pins,
                "total_pins_analyzed": analyzed_count
            })
            
            # Cleanup temporary config
            if os.path.exists(config_path):
                os.remove(config_path)
            
            logger.info(f"Completed scraping job {job_id}: {processed_pins} pins, {analyzed_count} analyzed")
            
        except Exception as e:
            logger.error(f"Scraping job {job_id} failed: {e}")
            
            # Mark job as failed
            await self.mongodb.update_job(job_id, {
                "status": JobStatus.FAILED.value,
                "error_message": str(e),
                "completed_at": datetime.utcnow()
            })
    
    async def _convert_pin_to_document(self, pin: PinData, job_id: str) -> PinDocument:
        """Convert PinData to PinDocument for database storage"""
        # Convert AI analysis to proper format
        ai_analysis = None
        if pin.ai_analysis:
            ai_analysis = pin.ai_analysis
        
        return PinDocument(
            pin_id=pin.pin_id,
            title=pin.title,
            description=pin.description,
            image_url=pin.image_url,
            local_image_path=pin.local_image_path,
            board_name=pin.board_name,
            board_url=pin.board_url,
            author=pin.author,
            save_count=pin.save_count,
            created_date=datetime.fromisoformat(pin.created_date) if pin.created_date else None,
            scraped_at=datetime.fromisoformat(pin.scraped_at),
            job_id=job_id,
            ai_analysis=ai_analysis,
            tags=pin.tags or []
        )
    
    async def get_job_status(self, job_id: str) -> Optional[ScrapingJobResponse]:
        """Get job status"""
        job_data = await self.mongodb.get_job(job_id)
        if not job_data:
            return None
        
        return ScrapingJobResponse(
            job_id=job_data['job_id'],
            status=JobStatus(job_data['status']),
            message=f"Job is {job_data['status']}",
            created_at=job_data['created_at'],
            updated_at=job_data.get('updated_at'),
            completed_at=job_data.get('completed_at'),
            job_name=job_data.get('job_name'),
            board_urls=job_data.get('board_urls', []),
            total_pins_scraped=job_data.get('total_pins_scraped', 0),
            total_pins_analyzed=job_data.get('total_pins_analyzed', 0),
            error_message=job_data.get('error_message'),
            progress_percentage=job_data.get('progress_percentage', 0.0),
            tags=job_data.get('tags', [])
        )
    
    async def list_jobs(self, skip: int, limit: int, status: Optional[JobStatus]) -> List[ScrapingJobResponse]:
        """List jobs with pagination"""
        jobs_data = await self.mongodb.list_jobs(skip, limit, status)
        
        jobs = []
        for job_data in jobs_data:
            job_response = ScrapingJobResponse(
                job_id=job_data['job_id'],
                status=JobStatus(job_data['status']),
                message=f"Job is {job_data['status']}",
                created_at=job_data['created_at'],
                updated_at=job_data.get('updated_at'),
                completed_at=job_data.get('completed_at'),
                job_name=job_data.get('job_name'),
                board_urls=job_data.get('board_urls', []),
                total_pins_scraped=job_data.get('total_pins_scraped', 0),
                total_pins_analyzed=job_data.get('total_pins_analyzed', 0),
                error_message=job_data.get('error_message'),
                progress_percentage=job_data.get('progress_percentage', 0.0),
                tags=job_data.get('tags', [])
            )
            jobs.append(job_response)
        
        return jobs
    
    async def get_job_pins(self, job_id: str, skip: int, limit: int) -> List[PinResponse]:
        """Get pins for a job"""
        pins_data = await self.mongodb.get_job_pins(job_id, skip, limit)
        
        pins = []
        for pin_data in pins_data:
            pin_response = await self._convert_pin_data_to_response(pin_data)
            pins.append(pin_response)
        
        return pins
    
    async def search_pins(self, filters: Dict, skip: int, limit: int) -> List[PinResponse]:
        """Search pins with filters"""
        pins_data = await self.mongodb.search_pins(filters, skip, limit)
        
        pins = []
        for pin_data in pins_data:
            pin_response = await self._convert_pin_data_to_response(pin_data)
            pins.append(pin_response)
        
        return pins
    
    async def get_pin(self, pin_id: str) -> Optional[PinResponse]:
        """Get a specific pin"""
        pin_data = await self.mongodb.get_pin(pin_id)
        if not pin_data:
            return None
        
        return await self._convert_pin_data_to_response(pin_data)
    
    async def _convert_pin_data_to_response(self, pin_data: Dict) -> PinResponse:
        """Convert database pin data to API response"""
        # Convert AI analysis if present
        ai_analysis = None
        if pin_data.get('ai_analysis'):
            ai_analysis_data = pin_data['ai_analysis']
            
            # Convert fashion items
            fashion_items = []
            for item in ai_analysis_data.get('fashion_items', []):
                fashion_item = FashionItem(
                    category=item.get('category', ''),
                    type=item.get('type', ''),
                    color=item.get('color', []),
                    material=item.get('material', ''),
                    style=item.get('style', ''),
                    brand=item.get('brand', ''),
                    confidence=item.get('confidence'),
                    fabric_details=item.get('fabric_details', []),
                    specific_type=item.get('specific_type'),
                    additional_attributes=item.get('additional_attributes', {}),
                    season_appropriateness=item.get('season_appropriateness', []),
                    occasion_suitability=item.get('occasion_suitability', []),
                    price_range_estimate=item.get('price_range_estimate'),
                    trend_status=item.get('trend_status')
                )
                fashion_items.append(fashion_item)
            
            ai_analysis = AIAnalysis(
                fashion_items=fashion_items,
                overall_outfit_analysis=ai_analysis_data.get('overall_outfit_analysis', {}),
                style_analysis=ai_analysis_data.get('style_analysis', {}),
                analysis_timestamp=datetime.utcnow(),  # Use current time if not stored
                confidence_score=ai_analysis_data.get('confidence_score')
            )
        
        return PinResponse(
            pin_id=pin_data['pin_id'],
            title=pin_data['title'],
            description=pin_data['description'],
            image_url=pin_data['image_url'],
            local_image_path=pin_data.get('local_image_path'),
            board_name=pin_data['board_name'],
            board_url=pin_data['board_url'],
            author=pin_data['author'],
            save_count=pin_data.get('save_count'),
            created_date=pin_data.get('created_date'),
            scraped_at=pin_data['scraped_at'],
            job_id=pin_data['job_id'],
            ai_analysis=ai_analysis,
            tags=pin_data.get('tags', [])
        )
    
    async def delete_job(self, job_id: str) -> bool:
        """Delete a job and its data"""
        return await self.mongodb.delete_job(job_id)
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics"""
        return await self.mongodb.get_statistics()
    
    # Analysis operations
    async def create_analysis_job(self, request: AnalysisRequest) -> str:
        """Create a new analysis job"""
        analysis_id = str(uuid.uuid4())
        
        analysis_data = AnalysisDocument(
            analysis_id=analysis_id,
            status="pending",
            created_at=datetime.utcnow(),
            image_url=str(request.image_url) if request.image_url else None,
            image_base64=request.image_base64,
            analysis_type=request.analysis_type
        )
        
        await self.mongodb.create_analysis(analysis_data)
        return analysis_id
    
    async def execute_analysis_job(self, analysis_id: str, request: AnalysisRequest):
        """Execute analysis job in background"""
        try:
            # Update status to running
            await self.mongodb.update_analysis(analysis_id, {"status": "running"})
            
            # Perform analysis
            result = await self._perform_ai_analysis(request)
            
            # Update with results
            await self.mongodb.update_analysis(analysis_id, {
                "status": "completed",
                "completed_at": datetime.utcnow(),
                "result": result
            })
            
        except Exception as e:
            logger.error(f"Analysis job {analysis_id} failed: {e}")
            await self.mongodb.update_analysis(analysis_id, {
                "status": "failed",
                "completed_at": datetime.utcnow(),
                "error_message": str(e)
            })
    
    async def analyze_image_sync(self, request: AnalysisRequest) -> AnalysisResponse:
        """Perform synchronous image analysis"""
        analysis_id = str(uuid.uuid4())
        
        try:
            result = await self._perform_ai_analysis(request)
            
            return AnalysisResponse(
                analysis_id=analysis_id,
                status="completed",
                ai_analysis=result,
                created_at=datetime.utcnow(),
                completed_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Sync analysis failed: {e}")
            return AnalysisResponse(
                analysis_id=analysis_id,
                status="failed",
                error_message=str(e),
                created_at=datetime.utcnow(),
                completed_at=datetime.utcnow()
            )
    
    async def _perform_ai_analysis(self, request: AnalysisRequest) -> Dict[str, Any]:
        """Perform AI analysis on image"""
        if not self.ai_analyzer:
            raise ValueError("AI analyzer not available")
        
        # Handle image input
        if request.image_url:
            # Download image temporarily for analysis
            import requests
            import tempfile
            
            response = requests.get(str(request.image_url))
            response.raise_for_status()
            
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
                tmp_file.write(response.content)
                image_path = tmp_file.name
            
            try:
                # Perform comprehensive analysis
                result = self.ai_analyzer.comprehensive_analysis(image_path)
                return result
            finally:
                # Cleanup temporary file
                os.unlink(image_path)
                
        elif request.image_base64:
            # Handle base64 image
            import base64
            import tempfile
            
            image_data = base64.b64decode(request.image_base64)
            
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
                tmp_file.write(image_data)
                image_path = tmp_file.name
            
            try:
                result = self.ai_analyzer.comprehensive_analysis(image_path)
                return result
            finally:
                os.unlink(image_path)
        
        else:
            raise ValueError("No image provided for analysis")
    
    async def get_analysis_result(self, analysis_id: str) -> Optional[AnalysisResponse]:
        """Get analysis result"""
        analysis_data = await self.mongodb.get_analysis(analysis_id)
        if not analysis_data:
            return None
        
        return AnalysisResponse(
            analysis_id=analysis_data['analysis_id'],
            status=analysis_data['status'],
            ai_analysis=analysis_data.get('result'),
            created_at=analysis_data['created_at'],
            completed_at=analysis_data.get('completed_at'),
            error_message=analysis_data.get('error_message')
        )
    
    async def export_training_dataset(self, job_id: str, format: str) -> Dict[str, Any]:
        """Export training dataset for a job"""
        # Get pins for the job
        pins_data = await self.mongodb.get_training_dataset(job_ids=[job_id])
        
        if format == "json":
            return {
                "format": "json",
                "data": pins_data,
                "total_samples": len(pins_data)
            }
        elif format == "csv":
            # Convert to CSV format
            import pandas as pd
            
            # Flatten the data for CSV
            flattened_data = []
            for pin in pins_data:
                flat_pin = {
                    "pin_id": pin["pin_id"],
                    "title": pin["title"],
                    "description": pin["description"],
                    "board_name": pin["board_name"],
                    "author": pin["author"],
                    "tags": ",".join(pin.get("tags", [])),
                    "scraped_at": pin["scraped_at"]
                }
                
                # Add AI analysis data if available
                if pin.get("ai_analysis"):
                    ai_data = pin["ai_analysis"]
                    fashion_items = ai_data.get("fashion_items", [])
                    
                    if fashion_items:
                        for i, item in enumerate(fashion_items):
                            flat_pin[f"item_{i}_category"] = item.get("category", "")
                            flat_pin[f"item_{i}_type"] = item.get("type", "")
                            flat_pin[f"item_{i}_colors"] = ",".join(item.get("color", []))
                            flat_pin[f"item_{i}_material"] = item.get("material", "")
                            flat_pin[f"item_{i}_style"] = item.get("style", "")
                
                flattened_data.append(flat_pin)
            
            df = pd.DataFrame(flattened_data)
            csv_data = df.to_csv(index=False)
            
            return {
                "format": "csv",
                "data": csv_data,
                "total_samples": len(flattened_data)
            }
        
        else:
            raise ValueError(f"Unsupported format: {format}")
