#!/usr/bin/env python3
"""
MongoDB database connection and operations for Pinterest Scraper API
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError
from typing import List, Dict, Optional, Any
import logging
from datetime import datetime
from bson import ObjectId
import json

from .models import JobDocument, PinDocument, AnalysisDocument, JobStatus

logger = logging.getLogger(__name__)

class MongoDB:
    """MongoDB async database manager"""
    
    def __init__(self, connection_string: str, database_name: str):
        self.connection_string = connection_string
        self.database_name = database_name
        self.client: AsyncIOMotorClient = None
        self.db = None
        
    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(self.connection_string)
            self.db = self.client[self.database_name]
            
            # Test connection
            await self.client.admin.command('ping')
            
            # Create indexes
            await self._create_indexes()
            
            logger.info(f"Connected to MongoDB: {self.database_name}")
            
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")
    
    async def health_check(self) -> bool:
        """Check database health"""
        try:
            await self.client.admin.command('ping')
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    async def _create_indexes(self):
        """Create database indexes for optimal performance"""
        try:
            # Jobs collection indexes
            await self.db.jobs.create_index("job_id", unique=True)
            await self.db.jobs.create_index("status")
            await self.db.jobs.create_index("created_at")
            await self.db.jobs.create_index("tags")
            
            # Pins collection indexes
            await self.db.pins.create_index("pin_id", unique=True)
            await self.db.pins.create_index("job_id")
            await self.db.pins.create_index("board_name")
            await self.db.pins.create_index("author")
            await self.db.pins.create_index("scraped_at")
            await self.db.pins.create_index("tags")
            await self.db.pins.create_index([("title", "text"), ("description", "text")])
            
            # Analysis collection indexes
            await self.db.analysis.create_index("analysis_id", unique=True)
            await self.db.analysis.create_index("status")
            await self.db.analysis.create_index("created_at")
            
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
    
    # Job operations
    async def create_job(self, job_data: JobDocument) -> str:
        """Create a new scraping job"""
        try:
            job_dict = job_data.dict()
            result = await self.db.jobs.insert_one(job_dict)
            logger.info(f"Created job: {job_data.job_id}")
            return job_data.job_id
            
        except DuplicateKeyError:
            raise ValueError(f"Job with ID {job_data.job_id} already exists")
        except Exception as e:
            logger.error(f"Failed to create job: {e}")
            raise
    
    async def get_job(self, job_id: str) -> Optional[Dict]:
        """Get job by ID"""
        try:
            job = await self.db.jobs.find_one({"job_id": job_id})
            if job:
                job.pop('_id', None)  # Remove MongoDB ObjectId
            return job
            
        except Exception as e:
            logger.error(f"Failed to get job {job_id}: {e}")
            return None
    
    async def update_job(self, job_id: str, update_data: Dict) -> bool:
        """Update job data"""
        try:
            update_data['updated_at'] = datetime.utcnow()
            
            result = await self.db.jobs.update_one(
                {"job_id": job_id},
                {"$set": update_data}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Failed to update job {job_id}: {e}")
            return False
    
    async def list_jobs(self, skip: int = 0, limit: int = 10, status: Optional[JobStatus] = None) -> List[Dict]:
        """List jobs with pagination and filtering"""
        try:
            query = {}
            if status:
                query['status'] = status.value
            
            cursor = self.db.jobs.find(query).sort("created_at", -1).skip(skip).limit(limit)
            jobs = []
            
            async for job in cursor:
                job.pop('_id', None)
                jobs.append(job)
            
            return jobs
            
        except Exception as e:
            logger.error(f"Failed to list jobs: {e}")
            return []
    
    async def delete_job(self, job_id: str) -> bool:
        """Delete job and associated pins"""
        try:
            # Delete associated pins first
            await self.db.pins.delete_many({"job_id": job_id})
            
            # Delete job
            result = await self.db.jobs.delete_one({"job_id": job_id})
            
            logger.info(f"Deleted job {job_id} and associated data")
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"Failed to delete job {job_id}: {e}")
            return False
    
    # Pin operations
    async def create_pin(self, pin_data: PinDocument) -> str:
        """Create a new pin"""
        try:
            pin_dict = pin_data.dict()
            
            # Handle duplicate pins gracefully
            existing = await self.db.pins.find_one({"pin_id": pin_data.pin_id})
            if existing:
                logger.warning(f"Pin {pin_data.pin_id} already exists, skipping")
                return pin_data.pin_id
            
            await self.db.pins.insert_one(pin_dict)
            return pin_data.pin_id
            
        except Exception as e:
            logger.error(f"Failed to create pin {pin_data.pin_id}: {e}")
            raise
    
    async def get_pin(self, pin_id: str) -> Optional[Dict]:
        """Get pin by ID"""
        try:
            pin = await self.db.pins.find_one({"pin_id": pin_id})
            if pin:
                pin.pop('_id', None)
            return pin
            
        except Exception as e:
            logger.error(f"Failed to get pin {pin_id}: {e}")
            return None
    
    async def get_job_pins(self, job_id: str, skip: int = 0, limit: int = 50) -> List[Dict]:
        """Get pins for a specific job"""
        try:
            cursor = self.db.pins.find({"job_id": job_id}).skip(skip).limit(limit)
            pins = []
            
            async for pin in cursor:
                pin.pop('_id', None)
                pins.append(pin)
            
            return pins
            
        except Exception as e:
            logger.error(f"Failed to get pins for job {job_id}: {e}")
            return []
    
    async def search_pins(self, filters: Dict, skip: int = 0, limit: int = 50) -> List[Dict]:
        """Search pins with filters"""
        try:
            query = {}
            
            # Text search
            if 'query' in filters:
                query['$text'] = {'$search': filters['query']}
            
            # Tag search
            if 'tags' in filters:
                query['tags'] = {'$in': filters['tags']}
            
            # Board name filter
            if 'board_name' in filters:
                query['board_name'] = {'$regex': filters['board_name'], '$options': 'i'}
            
            # Author filter
            if 'author' in filters:
                query['author'] = {'$regex': filters['author'], '$options': 'i'}
            
            # Date range filter
            if 'date_from' in filters or 'date_to' in filters:
                date_query = {}
                if 'date_from' in filters:
                    date_query['$gte'] = filters['date_from']
                if 'date_to' in filters:
                    date_query['$lte'] = filters['date_to']
                query['scraped_at'] = date_query
            
            # AI analysis filter
            if 'has_ai_analysis' in filters:
                if filters['has_ai_analysis']:
                    query['ai_analysis'] = {'$ne': None}
                else:
                    query['ai_analysis'] = None
            
            cursor = self.db.pins.find(query).skip(skip).limit(limit)
            pins = []
            
            async for pin in cursor:
                pin.pop('_id', None)
                pins.append(pin)
            
            return pins
            
        except Exception as e:
            logger.error(f"Failed to search pins: {e}")
            return []
    
    async def update_pin(self, pin_id: str, update_data: Dict) -> bool:
        """Update pin data"""
        try:
            result = await self.db.pins.update_one(
                {"pin_id": pin_id},
                {"$set": update_data}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Failed to update pin {pin_id}: {e}")
            return False
    
    # Analysis operations
    async def create_analysis(self, analysis_data: AnalysisDocument) -> str:
        """Create a new analysis job"""
        try:
            analysis_dict = analysis_data.dict()
            await self.db.analysis.insert_one(analysis_dict)
            return analysis_data.analysis_id
            
        except Exception as e:
            logger.error(f"Failed to create analysis: {e}")
            raise
    
    async def get_analysis(self, analysis_id: str) -> Optional[Dict]:
        """Get analysis by ID"""
        try:
            analysis = await self.db.analysis.find_one({"analysis_id": analysis_id})
            if analysis:
                analysis.pop('_id', None)
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to get analysis {analysis_id}: {e}")
            return None
    
    async def update_analysis(self, analysis_id: str, update_data: Dict) -> bool:
        """Update analysis data"""
        try:
            result = await self.db.analysis.update_one(
                {"analysis_id": analysis_id},
                {"$set": update_data}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Failed to update analysis {analysis_id}: {e}")
            return False
    
    # Statistics operations
    async def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics"""
        try:
            stats = {}
            
            # Job statistics
            stats['total_jobs'] = await self.db.jobs.count_documents({})
            
            # Jobs by status
            pipeline = [
                {"$group": {"_id": "$status", "count": {"$sum": 1}}}
            ]
            jobs_by_status = {}
            async for result in self.db.jobs.aggregate(pipeline):
                jobs_by_status[result['_id']] = result['count']
            stats['jobs_by_status'] = jobs_by_status
            
            # Pin statistics
            stats['total_pins_scraped'] = await self.db.pins.count_documents({})
            stats['total_pins_analyzed'] = await self.db.pins.count_documents({"ai_analysis": {"$ne": None}})
            
            # Top boards
            pipeline = [
                {"$group": {"_id": "$board_name", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 10}
            ]
            top_boards = []
            async for result in self.db.pins.aggregate(pipeline):
                top_boards.append({"board_name": result['_id'], "pin_count": result['count']})
            stats['top_boards'] = top_boards
            
            # Top tags
            pipeline = [
                {"$unwind": "$tags"},
                {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 20}
            ]
            top_tags = []
            async for result in self.db.pins.aggregate(pipeline):
                top_tags.append({"tag": result['_id'], "count": result['count']})
            stats['top_tags'] = top_tags
            
            # Storage statistics
            db_stats = await self.db.command("dbStats")
            stats['storage_stats'] = {
                "database_size_mb": round(db_stats.get('dataSize', 0) / (1024 * 1024), 2),
                "index_size_mb": round(db_stats.get('indexSize', 0) / (1024 * 1024), 2),
                "total_collections": db_stats.get('collections', 0)
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}
    
    # Bulk operations
    async def bulk_create_pins(self, pins_data: List[PinDocument]) -> int:
        """Create multiple pins in bulk"""
        try:
            if not pins_data:
                return 0
            
            pins_dict = [pin.dict() for pin in pins_data]
            
            # Use ordered=False to continue on duplicates
            result = await self.db.pins.insert_many(pins_dict, ordered=False)
            
            logger.info(f"Bulk created {len(result.inserted_ids)} pins")
            return len(result.inserted_ids)
            
        except Exception as e:
            logger.error(f"Failed to bulk create pins: {e}")
            return 0
    
    async def get_training_dataset(self, job_ids: Optional[List[str]] = None, filters: Optional[Dict] = None) -> List[Dict]:
        """Get training dataset with optional filters"""
        try:
            query = {"ai_analysis": {"$ne": None}}
            
            if job_ids:
                query["job_id"] = {"$in": job_ids}
            
            if filters:
                # Apply additional filters
                if 'tags' in filters:
                    query['tags'] = {'$in': filters['tags']}
                if 'board_name' in filters:
                    query['board_name'] = {'$regex': filters['board_name'], '$options': 'i'}
            
            cursor = self.db.pins.find(query)
            dataset = []
            
            async for pin in cursor:
                pin.pop('_id', None)
                dataset.append(pin)
            
            return dataset
            
        except Exception as e:
            logger.error(f"Failed to get training dataset: {e}")
            return []
