#!/usr/bin/env python3
"""
Pinterest Scraper Service Manager
Start/stop the automated Pinterest scraper service
"""

import os
import sys
import signal
import subprocess
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_requirements():
    """Check if required environment variables are set"""
    required_vars = ['DEFAULT_BOARD_URLS', 'PINTEREST_EMAIL', 'PINTEREST_PASSWORD']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n💡 Please update your .env file with the required values")
        return False
    
    return True

def start_automated_scraper():
    """Start the automated scraper service"""
    print("🚀 Starting Pinterest Automated Scraper Service")
    print("=" * 50)
    
    # Check requirements
    if not check_requirements():
        return
    
    # Display configuration
    board_urls = os.getenv('DEFAULT_BOARD_URLS', '').split(',')
    check_interval = os.getenv('CHECK_INTERVAL_MINUTES', '30')
    
    print(f"📋 Monitoring {len(board_urls)} Pinterest boards:")
    for i, url in enumerate(board_urls, 1):
        print(f"   {i}. {url.strip()}")
    
    print(f"⏰ Check interval: {check_interval} minutes")
    print(f"🤖 AI Analysis: {'Enabled' if os.getenv('ENABLE_AI_ANALYSIS', 'true').lower() == 'true' else 'Disabled'}")
    print(f"📊 Logs: automated_scraper.log")
    print(f"💾 Data: scraped_data/ directory")
    print()
    print("🛑 Press Ctrl+C to stop the service")
    print("=" * 50)
    
    try:
        # Start the automated scraper
        subprocess.run([sys.executable, 'automated_scraper.py'], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Service stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Service failed with error: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

def show_status():
    """Show current scraper status and statistics"""
    print("📊 Pinterest Scraper Status")
    print("=" * 30)
    
    # Check if tracker file exists
    tracker_file = 'scraped_pins_tracker.json'
    if os.path.exists(tracker_file):
        import json
        try:
            with open(tracker_file, 'r') as f:
                data = json.load(f)
            
            print(f"📌 Total pins scraped: {data.get('total_pins', 0)}")
            print(f"🕒 Last updated: {data.get('last_updated', 'Never')}")
            
        except Exception as e:
            print(f"❌ Error reading tracker file: {e}")
    else:
        print("📌 No scraping data found yet")
    
    # Check if log file exists
    log_file = 'automated_scraper.log'
    if os.path.exists(log_file):
        print(f"📋 Log file: {log_file}")
        
        # Show last few log lines
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
                if lines:
                    print("\n📝 Recent activity:")
                    for line in lines[-5:]:
                        print(f"   {line.strip()}")
        except Exception as e:
            print(f"❌ Error reading log file: {e}")
    else:
        print("📋 No log file found")

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("🎯 Pinterest Scraper Service Manager")
        print("=" * 40)
        print("Usage:")
        print("  python start_scraper.py start    - Start automated scraper")
        print("  python start_scraper.py status   - Show scraper status")
        print("  python start_scraper.py config   - Show configuration")
        print()
        print("💡 The scraper will automatically monitor your Pinterest boards")
        print("   and scrape new pins every 30 minutes (configurable)")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'start':
        start_automated_scraper()
    elif command == 'status':
        show_status()
    elif command == 'config':
        print("⚙️  Current Configuration")
        print("=" * 25)
        print(f"📋 Board URLs: {os.getenv('DEFAULT_BOARD_URLS', 'Not set')}")
        print(f"⏰ Check interval: {os.getenv('CHECK_INTERVAL_MINUTES', '30')} minutes")
        print(f"🤖 AI Analysis: {os.getenv('ENABLE_AI_ANALYSIS', 'true')}")
        print(f"📧 Pinterest email: {os.getenv('PINTEREST_EMAIL', 'Not set')}")
        print(f"🔑 Gemini API key: {'Set' if os.getenv('GEMINI_API_KEY') else 'Not set'}")
    else:
        print(f"❌ Unknown command: {command}")
        print("Available commands: start, status, config")

if __name__ == "__main__":
    main()
