#!/usr/bin/env python3
"""
Production Pinterest Scraping Pipeline
Addresses Saurav's requirements for a robust, sustainable backend pipeline
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from typing import Dict, List
from pinterest_scraper import PinterestScraper
from image_downloader import ImageDownloader
from database import PinterestDatabase
from pinterest_auth import PinterestAuth

class ProductionPinterestPipeline:
    def __init__(self):
        self.setup_logging()
        self.db = PinterestDatabase()
        self.image_downloader = ImageDownloader()
        self.scraper = None
        self.stats = {
            'total_pins_scraped': 0,
            'total_images_downloaded': 0,
            'total_boards_processed': 0,
            'success_rate': 0.0,
            'start_time': datetime.now(),
            'boards_stats': []
        }
    
    def setup_logging(self):
        """Setup comprehensive logging for production"""
        log_filename = f"production_pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filename),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info("=== Production Pinterest Pipeline Started ===")
    
    def initialize_scraper(self):
        """Initialize scraper with authentication and anti-detection measures"""
        try:
            self.logger.info("Initializing Pinterest scraper with authentication...")
            self.scraper = PinterestScraper(headless=True, delay=2)
            
            # Attempt authentication
            auth = PinterestAuth(self.scraper.driver)
            if auth.login():
                self.logger.info("✅ Successfully authenticated with Pinterest")
                return True
            else:
                self.logger.warning("⚠️  Authentication failed, proceeding without login")
                return True  # Continue anyway, might still work for some boards
                
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize scraper: {e}")
            return False
    
    def load_target_boards(self) -> List[str]:
        """Load target Pinterest boards from configuration"""
        try:
            with open('board_urls.json', 'r') as f:
                config = json.load(f)
                board_urls = config.get('board_urls', [])
            
            self.logger.info(f"Loaded {len(board_urls)} target boards:")
            for i, url in enumerate(board_urls, 1):
                self.logger.info(f"  {i}. {url}")
            
            return board_urls
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load board configuration: {e}")
            return []
    
    def scrape_board_with_resilience(self, board_url: str, max_pins: int = 200) -> Dict:
        """Scrape a board with resilience and retry logic"""
        self.logger.info(f"🎯 Starting scrape for board: {board_url}")
        
        # Get existing pins to avoid duplicates
        existing_pins = self.db.get_all_pins()
        existing_pin_ids = {pin['pin_id'] for pin in existing_pins if pin.get('pin_id')}
        self.logger.info(f"Found {len(existing_pin_ids)} existing pins in database")
        
        retry_count = 0
        max_retries = 3
        
        while retry_count < max_retries:
            try:
                # Scrape the board
                result = self.scraper.scrape_board(board_url, max_pins)
                
                if 'error' in result:
                    self.logger.warning(f"⚠️  Scraping attempt {retry_count + 1} failed: {result['error']}")
                    retry_count += 1
                    if retry_count < max_retries:
                        wait_time = 30 * retry_count  # Exponential backoff
                        self.logger.info(f"Waiting {wait_time} seconds before retry...")
                        time.sleep(wait_time)
                    continue
                
                # Filter out existing pins
                all_pins = result.get('pins', [])
                new_pins = [pin for pin in all_pins if pin.get('pin_id') not in existing_pin_ids]
                
                self.logger.info(f"📊 Scraping results:")
                self.logger.info(f"  Total pins found: {len(all_pins)}")
                self.logger.info(f"  New pins: {len(new_pins)}")
                self.logger.info(f"  Duplicates skipped: {len(all_pins) - len(new_pins)}")
                
                # Save new pins to database
                saved_count = 0
                for pin in new_pins:
                    try:
                        pin['board_url'] = board_url
                        pin['scraped_date'] = datetime.now().isoformat()
                        self.db.save_pin(pin)
                        saved_count += 1
                    except Exception as e:
                        self.logger.warning(f"Failed to save pin {pin.get('pin_id', 'unknown')}: {e}")
                
                self.logger.info(f"💾 Saved {saved_count} new pins to database")
                
                # Download images for new pins
                download_results = {}
                if new_pins:
                    self.logger.info(f"📥 Starting image download for {len(new_pins)} new pins...")
                    download_results = self.image_downloader.download_pin_images(new_pins)
                    
                    downloaded = download_results.get('downloaded', 0)
                    failed = download_results.get('failed', 0)
                    total_attempts = downloaded + failed
                    success_rate = (downloaded / total_attempts * 100) if total_attempts > 0 else 0
                    
                    self.logger.info(f"📥 Image download results:")
                    self.logger.info(f"  Downloaded: {downloaded}")
                    self.logger.info(f"  Failed: {failed}")
                    self.logger.info(f"  Success rate: {success_rate:.1f}%")
                    self.logger.info(f"  Thumbnails: {download_results.get('thumbnails_created', 0)}")
                
                # Return comprehensive results
                return {
                    'board_url': board_url,
                    'success': True,
                    'pins_found': len(all_pins),
                    'new_pins': len(new_pins),
                    'pins_saved': saved_count,
                    'download_results': download_results,
                    'retry_count': retry_count
                }
                
            except Exception as e:
                self.logger.error(f"❌ Unexpected error during scraping attempt {retry_count + 1}: {e}")
                retry_count += 1
                if retry_count < max_retries:
                    wait_time = 60 * retry_count
                    self.logger.info(f"Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
        
        # All retries failed
        self.logger.error(f"❌ Failed to scrape board after {max_retries} attempts: {board_url}")
        return {
            'board_url': board_url,
            'success': False,
            'error': f'Failed after {max_retries} retry attempts',
            'pins_found': 0,
            'new_pins': 0,
            'pins_saved': 0,
            'download_results': {},
            'retry_count': max_retries
        }
    
    def run_production_pipeline(self):
        """Run the complete production pipeline"""
        self.logger.info("🚀 Starting Production Pinterest Pipeline")
        
        try:
            # Initialize scraper
            if not self.initialize_scraper():
                self.logger.error("❌ Failed to initialize scraper, aborting pipeline")
                return False
            
            # Load target boards
            board_urls = self.load_target_boards()
            if not board_urls:
                self.logger.error("❌ No boards to scrape, aborting pipeline")
                return False
            
            # Process each board
            total_new_pins = 0
            total_images_downloaded = 0
            
            for i, board_url in enumerate(board_urls, 1):
                self.logger.info(f"\n📋 Processing board {i}/{len(board_urls)}")
                
                # Scrape board with resilience
                result = self.scrape_board_with_resilience(board_url, max_pins=200)
                
                # Update statistics
                self.stats['boards_stats'].append(result)
                if result['success']:
                    total_new_pins += result['new_pins']
                    download_results = result.get('download_results', {})
                    total_images_downloaded += download_results.get('downloaded', 0)
                
                # Add delay between boards to avoid rate limiting
                if i < len(board_urls):
                    delay = 30  # 30 seconds between boards
                    self.logger.info(f"⏳ Waiting {delay} seconds before next board...")
                    time.sleep(delay)
            
            # Calculate final statistics
            self.stats['total_pins_scraped'] = total_new_pins
            self.stats['total_images_downloaded'] = total_images_downloaded
            self.stats['total_boards_processed'] = len(board_urls)
            
            successful_boards = sum(1 for result in self.stats['boards_stats'] if result['success'])
            self.stats['success_rate'] = (successful_boards / len(board_urls) * 100) if board_urls else 0
            
            # Generate final report
            self.generate_final_report()
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Pipeline failed with error: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        finally:
            # Clean up
            if self.scraper:
                try:
                    self.scraper.close()
                except:
                    pass
    
    def generate_final_report(self):
        """Generate comprehensive final report"""
        end_time = datetime.now()
        duration = end_time - self.stats['start_time']
        
        self.logger.info("\n" + "="*60)
        self.logger.info("📊 PRODUCTION PIPELINE FINAL REPORT")
        self.logger.info("="*60)
        
        self.logger.info(f"⏱️  Duration: {duration}")
        self.logger.info(f"📋 Boards processed: {self.stats['total_boards_processed']}")
        self.logger.info(f"📌 New pins scraped: {self.stats['total_pins_scraped']}")
        self.logger.info(f"📥 Images downloaded: {self.stats['total_images_downloaded']}")
        self.logger.info(f"✅ Success rate: {self.stats['success_rate']:.1f}%")
        
        # Board-by-board breakdown
        self.logger.info(f"\n📋 Board-by-board results:")
        for i, result in enumerate(self.stats['boards_stats'], 1):
            status = "✅ SUCCESS" if result['success'] else "❌ FAILED"
            self.logger.info(f"  {i}. {status} - {result['new_pins']} new pins")
            self.logger.info(f"     {result['board_url']}")
        
        # Image download statistics
        image_stats = self.image_downloader.get_download_stats()
        self.logger.info(f"\n📁 Storage statistics:")
        self.logger.info(f"  Total images: {image_stats.get('total_images', 0)}")
        self.logger.info(f"  Total thumbnails: {image_stats.get('total_thumbnails', 0)}")
        self.logger.info(f"  Storage size: {image_stats.get('total_size_mb', 0)} MB")
        self.logger.info(f"  Directory: {image_stats.get('download_directory', 'N/A')}")
        
        # Database statistics
        all_pins = self.db.get_all_pins()
        self.logger.info(f"\n💾 Database statistics:")
        self.logger.info(f"  Total pins in database: {len(all_pins)}")
        
        # Save report to file
        report_data = {
            'timestamp': end_time.isoformat(),
            'duration_seconds': duration.total_seconds(),
            'stats': self.stats,
            'image_stats': image_stats,
            'database_stats': {'total_pins': len(all_pins)}
        }
        
        report_filename = f"pipeline_report_{end_time.strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        self.logger.info(f"\n📄 Detailed report saved to: {report_filename}")
        self.logger.info("="*60)

def main():
    """Main entry point for production pipeline"""
    pipeline = ProductionPinterestPipeline()
    
    try:
        success = pipeline.run_production_pipeline()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        pipeline.logger.info("\n⚠️  Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        pipeline.logger.error(f"❌ Pipeline crashed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
