#!/usr/bin/env python3
"""
Authentication module for Pinterest Scraper API
"""

from fastapi import HTTPException, status
from typing import Optional
import os
import hashlib
import secrets
from datetime import datetime, timedelta
import jwt
import logging

logger = logging.getLogger(__name__)

class APIKeyManager:
    """Manage API keys for authentication"""
    
    def __init__(self):
        # In production, store these in environment variables or secure storage
        self.valid_api_keys = set()
        self.load_api_keys()
    
    def load_api_keys(self):
        """Load API keys from environment or config"""
        # Default API key for development (change in production)
        default_key = os.getenv("PINTEREST_API_KEY", "dev-key-12345")
        self.valid_api_keys.add(default_key)
        
        # Load additional keys from environment
        additional_keys = os.getenv("ADDITIONAL_API_KEYS", "")
        if additional_keys:
            for key in additional_keys.split(","):
                if key.strip():
                    self.valid_api_keys.add(key.strip())
        
        logger.info(f"Loaded {len(self.valid_api_keys)} API keys")
    
    def generate_api_key(self) -> str:
        """Generate a new API key"""
        return secrets.token_urlsafe(32)
    
    def add_api_key(self, api_key: str):
        """Add a new API key"""
        self.valid_api_keys.add(api_key)
    
    def remove_api_key(self, api_key: str):
        """Remove an API key"""
        self.valid_api_keys.discard(api_key)
    
    def is_valid(self, api_key: str) -> bool:
        """Check if API key is valid"""
        return api_key in self.valid_api_keys

# Global API key manager
api_key_manager = APIKeyManager()

async def verify_api_key(api_key: str) -> bool:
    """Verify API key"""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not api_key_manager.is_valid(api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return True

class JWTManager:
    """JWT token management for enhanced security"""
    
    def __init__(self, secret_key: Optional[str] = None):
        self.secret_key = secret_key or os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 60 * 24  # 24 hours
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """Create JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        
        return encoded_jwt
    
    def verify_token(self, token: str) -> dict:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )

# Global JWT manager
jwt_manager = JWTManager()

def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return hash_password(password) == hashed_password
