#!/usr/bin/env python3
"""
Configuration management for Pinterest Scraper API
"""

from pydantic import BaseSettings, Field
from typing import Optional, List
import os
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    app_name: str = Field("Pinterest Scraper API", env="APP_NAME")
    app_version: str = Field("1.0.0", env="APP_VERSION")
    debug: bool = Field(False, env="DEBUG")
    
    # Server Configuration
    host: str = Field("0.0.0.0", env="HOST")
    port: int = Field(8000, env="PORT")
    workers: int = Field(1, env="WORKERS")
    
    # Database Configuration
    mongodb_url: str = Field("mongodb://localhost:27017", env="MONGODB_URL")
    database_name: str = Field("pinterest_scraper", env="DATABASE_NAME")
    
    # Pinterest Configuration
    pinterest_email: str = Field("", env="PINTEREST_EMAIL")
    pinterest_password: str = Field("", env="PINTEREST_PASSWORD")
    
    # AI Configuration
    gemini_api_key: str = Field("", env="GEMINI_API_KEY")
    
    # Default Pinterest Boards
    default_board_urls: List[str] = Field([], env="DEFAULT_BOARD_URLS")
    
    def get_default_boards(self) -> List[str]:
        """Parse comma-separated board URLs from environment"""
        if isinstance(self.default_board_urls, str):
            return [url.strip() for url in self.default_board_urls.split(',') if url.strip()]
        return self.default_board_urls or []
    
    # Security Configuration
    api_key: str = Field("dev-key-12345", env="API_KEY")
    jwt_secret_key: str = Field("your-secret-key-change-in-production", env="JWT_SECRET_KEY")
    
    # AWS Configuration
    aws_access_key_id: Optional[str] = Field(None, env="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = Field(None, env="AWS_SECRET_ACCESS_KEY")
    aws_region: str = Field("us-east-1", env="AWS_REGION")
    s3_bucket_name: Optional[str] = Field(None, env="S3_BUCKET_NAME")
    
    # File Storage Configuration
    upload_dir: str = Field("uploads", env="UPLOAD_DIR")
    max_file_size: int = Field(10 * 1024 * 1024, env="MAX_FILE_SIZE")  # 10MB
    allowed_extensions: List[str] = Field(["jpg", "jpeg", "png", "gif", "webp"], env="ALLOWED_EXTENSIONS")
    
    # Scraping Configuration
    default_max_pins: int = Field(100, env="DEFAULT_MAX_PINS")
    request_delay: int = Field(2, env="REQUEST_DELAY")
    max_concurrent_jobs: int = Field(5, env="MAX_CONCURRENT_JOBS")
    job_timeout_hours: int = Field(24, env="JOB_TIMEOUT_HOURS")
    
    # Logging Configuration
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_file: Optional[str] = Field(None, env="LOG_FILE")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

# AWS Configuration for deployment
class AWSConfig:
    """AWS-specific configuration"""
    
    @staticmethod
    def get_ecs_task_definition():
        """ECS task definition for deployment"""
        return {
            "family": "pinterest-scraper-api",
            "networkMode": "awsvpc",
            "requiresCompatibilities": ["FARGATE"],
            "cpu": "1024",
            "memory": "2048",
            "executionRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskExecutionRole",
            "taskRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskRole",
            "containerDefinitions": [
                {
                    "name": "pinterest-scraper-api",
                    "image": "pinterest-scraper-api:latest",
                    "portMappings": [
                        {
                            "containerPort": 8000,
                            "protocol": "tcp"
                        }
                    ],
                    "environment": [
                        {"name": "MONGODB_URL", "value": "mongodb://mongodb:27017"},
                        {"name": "DATABASE_NAME", "value": "pinterest_scraper"},
                        {"name": "HOST", "value": "0.0.0.0"},
                        {"name": "PORT", "value": "8000"}
                    ],
                    "secrets": [
                        {
                            "name": "PINTEREST_EMAIL",
                            "valueFrom": "arn:aws:secretsmanager:REGION:ACCOUNT:secret:pinterest-credentials:email"
                        },
                        {
                            "name": "PINTEREST_PASSWORD",
                            "valueFrom": "arn:aws:secretsmanager:REGION:ACCOUNT:secret:pinterest-credentials:password"
                        },
                        {
                            "name": "GEMINI_API_KEY",
                            "valueFrom": "arn:aws:secretsmanager:REGION:ACCOUNT:secret:gemini-api-key"
                        },
                        {
                            "name": "API_KEY",
                            "valueFrom": "arn:aws:secretsmanager:REGION:ACCOUNT:secret:api-key"
                        }
                    ],
                    "logConfiguration": {
                        "logDriver": "awslogs",
                        "options": {
                            "awslogs-group": "/ecs/pinterest-scraper-api",
                            "awslogs-region": "us-east-1",
                            "awslogs-stream-prefix": "ecs"
                        }
                    },
                    "healthCheck": {
                        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
                        "interval": 30,
                        "timeout": 5,
                        "retries": 3,
                        "startPeriod": 60
                    }
                }
            ]
        }
    
    @staticmethod
    def get_service_definition():
        """ECS service definition"""
        return {
            "serviceName": "pinterest-scraper-api",
            "cluster": "pinterest-scraper-cluster",
            "taskDefinition": "pinterest-scraper-api",
            "desiredCount": 2,
            "launchType": "FARGATE",
            "networkConfiguration": {
                "awsvpcConfiguration": {
                    "subnets": ["subnet-12345", "subnet-67890"],
                    "securityGroups": ["sg-12345"],
                    "assignPublicIp": "ENABLED"
                }
            },
            "loadBalancers": [
                {
                    "targetGroupArn": "arn:aws:elasticloadbalancing:REGION:ACCOUNT:targetgroup/pinterest-api/1234567890123456",
                    "containerName": "pinterest-scraper-api",
                    "containerPort": 8000
                }
            ],
            "healthCheckGracePeriodSeconds": 300
        }

# Environment-specific configurations
class EnvironmentConfig:
    """Environment-specific settings"""
    
    @staticmethod
    def get_development_config():
        """Development environment configuration"""
        return {
            "debug": True,
            "mongodb_url": "mongodb://localhost:27017",
            "log_level": "DEBUG",
            "cors_origins": ["http://localhost:3000", "http://localhost:8080"],
            "rate_limit": "1000/minute"
        }
    
    @staticmethod
    def get_staging_config():
        """Staging environment configuration"""
        return {
            "debug": False,
            "mongodb_url": "mongodb://staging-mongodb:27017",
            "log_level": "INFO",
            "cors_origins": ["https://staging.example.com"],
            "rate_limit": "500/minute"
        }
    
    @staticmethod
    def get_production_config():
        """Production environment configuration"""
        return {
            "debug": False,
            "mongodb_url": "mongodb://prod-mongodb:27017",
            "log_level": "WARNING",
            "cors_origins": ["https://api.example.com"],
            "rate_limit": "100/minute",
            "enable_https": True,
            "ssl_cert_path": "/etc/ssl/certs/api.crt",
            "ssl_key_path": "/etc/ssl/private/api.key"
        }
