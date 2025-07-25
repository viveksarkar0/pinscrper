#!/usr/bin/env python3
"""
Test script to run Pinterest scraping via API
"""

import requests
import json
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
API_BASE_URL = "http://localhost:8000"
API_KEY = os.getenv("API_KEY", "dev-api-key-12345")

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def test_health():
    """Test API health"""
    print("🔍 Testing API health...")
    response = requests.get(f"{API_BASE_URL}/health", headers=headers)
    if response.status_code == 200:
        print("✅ API is healthy!")
        print(f"   Response: {response.json()}")
    else:
        print(f"❌ API health check failed: {response.status_code}")
        return False
    return True

def start_scraping_job(board_urls, max_pins=50):
    """Start a scraping job"""
    print(f"🚀 Starting scraping job for {len(board_urls)} boards...")
    
    payload = {
        "board_urls": board_urls,
        "max_pins": max_pins,
        "analyze_with_ai": True
    }
    
    response = requests.post(f"{API_BASE_URL}/scrape", headers=headers, json=payload)
    
    if response.status_code == 200:
        job_data = response.json()
        print(f"✅ Job started successfully!")
        print(f"   Job ID: {job_data['job_id']}")
        print(f"   Status: {job_data['status']}")
        print(f"   Message: {job_data['message']}")
        return job_data['job_id']
    else:
        print(f"❌ Failed to start job: {response.status_code}")
        print(f"   Error: {response.text}")
        return None

def check_job_status(job_id):
    """Check job status"""
    print(f"📊 Checking status for job: {job_id}")
    
    response = requests.get(f"{API_BASE_URL}/jobs/{job_id}", headers=headers)
    
    if response.status_code == 200:
        job_data = response.json()
        print(f"   Status: {job_data['status']}")
        print(f"   Progress: {job_data.get('progress', 0)}%")
        print(f"   Pins scraped: {job_data.get('pins_scraped', 0)}")
        print(f"   Message: {job_data.get('message', 'No message')}")
        return job_data
    else:
        print(f"❌ Failed to get job status: {response.status_code}")
        return None

def list_all_jobs():
    """List all jobs"""
    print("📋 Listing all jobs...")
    
    response = requests.get(f"{API_BASE_URL}/jobs", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Total jobs: {data['total']}")
        for job in data['jobs']:
            print(f"   - Job {job['job_id']}: {job['status']} ({job.get('pins_scraped', 0)} pins)")
        return data
    else:
        print(f"❌ Failed to list jobs: {response.status_code}")
        return None

def list_pins():
    """List scraped pins"""
    print("📌 Listing scraped pins...")
    
    response = requests.get(f"{API_BASE_URL}/pins", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Total pins: {data['total']}")
        for pin in data['pins']:
            print(f"   - Pin {pin['pin_id']}: {pin['title']}")
            print(f"     URL: {pin['url']}")
            print(f"     Board: {pin['board_name']}")
        return data
    else:
        print(f"❌ Failed to list pins: {response.status_code}")
        return None

def main():
    """Main test function"""
    print("🎯 Pinterest Scraper API Test")
    print("=" * 40)
    
    # Test API health
    if not test_health():
        return
    
    print()
    
    # Example board URLs (replace with your actual Pinterest board URLs)
    board_urls = [
        "https://pinterest.com/username/fashion-inspiration",
        "https://pinterest.com/username/street-style",
        "https://pinterest.com/username/winter-fashion"
    ]
    
    # You can also use default boards from environment
    default_boards = os.getenv("DEFAULT_BOARD_URLS", "").split(",")
    if default_boards and default_boards[0].strip():
        board_urls = [url.strip() for url in default_boards if url.strip()]
        print(f"📂 Using default boards from environment: {len(board_urls)} boards")
    
    print(f"📋 Board URLs to scrape:")
    for i, url in enumerate(board_urls, 1):
        print(f"   {i}. {url}")
    
    print()
    
    # Start scraping job
    job_id = start_scraping_job(board_urls, max_pins=30)
    
    if job_id:
        print()
        
        # Check job status
        check_job_status(job_id)
        
        print()
        
        # List all jobs
        list_all_jobs()
        
        print()
        
        # List pins
        list_pins()
    
    print()
    print("🎉 Test completed!")
    print()
    print("💡 To customize board URLs:")
    print("   1. Edit the board_urls list in this script")
    print("   2. Or set DEFAULT_BOARD_URLS in your .env file")
    print("   3. Or make direct API calls with your board URLs")

if __name__ == "__main__":
    main()
