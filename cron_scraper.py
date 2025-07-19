#!/usr/bin/env python3
"""
Cron job script for daily Pinterest scraping
This script runs the Pinterest scraper daily to collect new pins from specified boards
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Set
import sqlite3

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pinterest_scraper import PinterestScraper
from database import PinterestDatabase
from image_downloader import ImageDownloader

class CronScraper:
    def __init__(self):
        self.setup_logging()
        self.db = PinterestDatabase()
        self.scraper = PinterestScraper(headless=True)
        self.image_downloader = ImageDownloader()
        
    def setup_logging(self):
        """Setup logging for cron job"""
        log_filename = f"cron_scraper_{datetime.now().strftime('%Y%m%d')}.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filename),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def load_board_urls(self) -> List[str]:
        """Load board URLs from configuration file or database"""
        try:
            # Try to load from config file first
            if os.path.exists('board_urls.json'):
                with open('board_urls.json', 'r') as f:
                    config = json.load(f)
                    return config.get('board_urls', [])
            
            # Fallback to hardcoded URLs (you should update these)
            default_boards = [
                # Add your Pinterest board URLs here
                # Example: "https://pinterest.com/username/board-name/"
            ]
            
            if not default_boards:
                self.logger.warning("No board URLs configured. Please create board_urls.json or update default_boards")
                
            return default_boards
            
        except Exception as e:
            self.logger.error(f"Error loading board URLs: {e}")
            return []
    
    def get_existing_pin_ids(self) -> Set[str]:
        """Get set of existing pin IDs from database to avoid duplicates"""
        try:
            existing_pins = self.db.get_all_pins()
            return {pin['pin_id'] for pin in existing_pins if pin.get('pin_id')}
        except Exception as e:
            self.logger.error(f"Error getting existing pin IDs: {e}")
            return set()
    
    def scrape_new_pins(self, board_url: str, existing_pin_ids: Set[str]) -> Dict:
        """Scrape a board and filter out existing pins"""
        self.logger.info(f"Starting daily scrape for board: {board_url}")
        
        try:
            # Scrape the board
            result = self.scraper.scrape_board(board_url, max_pins=2000)
            
            if 'error' in result:
                self.logger.error(f"Error scraping board {board_url}: {result['error']}")
                return result
            
            # Filter out existing pins
            new_pins = []
            for pin in result['pins']:
                if pin.get('pin_id') not in existing_pin_ids:
                    new_pins.append(pin)
            
            result['new_pins'] = new_pins
            result['new_pins_count'] = len(new_pins)
            result['total_pins_found'] = len(result['pins'])
            
            self.logger.info(f"Found {len(new_pins)} new pins out of {len(result['pins'])} total pins")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error during scraping: {e}")
            return {
                'board_url': board_url,
                'error': str(e),
                'new_pins': [],
                'new_pins_count': 0
            }
    
    def save_new_pins(self, board_result: Dict) -> int:
        """Save new pins to database"""
        try:
            if 'new_pins' not in board_result or not board_result['new_pins']:
                return 0
                
            saved_count = 0
            for pin in board_result['new_pins']:
                try:
                    # Add board URL to pin data
                    pin['board_url'] = board_result['board_url']
                    pin['scraped_date'] = datetime.now().isoformat()
                    
                    # Save to database
                    self.db.save_pin(pin)
                    saved_count += 1
                    
                except Exception as e:
                    self.logger.warning(f"Error saving pin {pin.get('pin_id', 'unknown')}: {e}")
                    continue
            
            self.logger.info(f"Successfully saved {saved_count} new pins to database")
            
            # Download images for new pins
            if board_result['new_pins']:
                self.logger.info(f"Starting image download for {len(board_result['new_pins'])} new pins...")
                download_results = self.image_downloader.download_pin_images(board_result['new_pins'])
                
                self.logger.info(f"Image download results:")
                self.logger.info(f"  Downloaded: {download_results.get('downloaded', 0)}")
                self.logger.info(f"  Failed: {download_results.get('failed', 0)}")
                self.logger.info(f"  Thumbnails: {download_results.get('thumbnails_created', 0)}")
                
                # Calculate success rate
                total_attempts = download_results.get('downloaded', 0) + download_results.get('failed', 0)
                if total_attempts > 0:
                    success_rate = (download_results.get('downloaded', 0) / total_attempts) * 100
                    self.logger.info(f"  Success rate: {success_rate:.1f}%")
            
            return saved_count
            
        except Exception as e:
            self.logger.error(f"Error saving pins: {e}")
            return 0
    
    def run_daily_scrape(self):
        """Main function to run daily scraping job"""
        start_time = datetime.now()
        self.logger.info(f"Starting daily Pinterest scrape at {start_time}")
        
        try:
            # Load board URLs
            board_urls = self.load_board_urls()
            if not board_urls:
                self.logger.error("No board URLs to scrape")
                return
            
            # Get existing pin IDs to avoid duplicates
            existing_pin_ids = self.get_existing_pin_ids()
            self.logger.info(f"Found {len(existing_pin_ids)} existing pins in database")
            
            total_new_pins = 0
            results = []
            
            # Scrape each board
            for board_url in board_urls:
                try:
                    # Scrape board and filter new pins
                    result = self.scrape_new_pins(board_url, existing_pin_ids)
                    results.append(result)
                    
                    # Save new pins to database
                    if 'new_pins' in result:
                        saved_count = self.save_new_pins(result)
                        total_new_pins += saved_count
                        
                        # Update existing pin IDs set for next board
                        for pin in result['new_pins']:
                            if pin.get('pin_id'):
                                existing_pin_ids.add(pin['pin_id'])
                    
                except Exception as e:
                    self.logger.error(f"Error processing board {board_url}: {e}")
                    continue
            
            # Log summary
            end_time = datetime.now()
            duration = end_time - start_time
            
            self.logger.info(f"Daily scrape completed in {duration}")
            self.logger.info(f"Total new pins collected: {total_new_pins}")
            self.logger.info(f"Boards processed: {len(results)}")
            
            # Save summary to file
            summary = {
                'date': start_time.isoformat(),
                'duration_seconds': duration.total_seconds(),
                'total_new_pins': total_new_pins,
                'boards_processed': len(results),
                'results': results
            }
            
            summary_filename = f"daily_scrape_summary_{start_time.strftime('%Y%m%d')}.json"
            with open(summary_filename, 'w') as f:
                json.dump(summary, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Fatal error during daily scrape: {e}")
            raise
        finally:
            # Clean up
            try:
                self.scraper.close()
            except:
                pass
    
    def cleanup_old_logs(self, days_to_keep: int = 7):
        """Clean up old log files"""
        try:
            current_time = datetime.now()
            for filename in os.listdir('.'):
                if filename.startswith('cron_scraper_') and filename.endswith('.log'):
                    file_path = os.path.join('.', filename)
                    file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                    if (current_time - file_time).days > days_to_keep:
                        os.remove(file_path)
                        self.logger.info(f"Removed old log file: {filename}")
        except Exception as e:
            self.logger.warning(f"Error cleaning up old logs: {e}")

def main():
    """Main entry point for cron job"""
    try:
        scraper = CronScraper()
        scraper.run_daily_scrape()
        scraper.cleanup_old_logs()
        
    except Exception as e:
        logging.error(f"Cron job failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
