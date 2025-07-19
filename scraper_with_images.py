#!/usr/bin/env python3
"""
Enhanced Pinterest scraper with image downloading capability
"""

import sys
import os
from pinterest_scraper import PinterestScraper
from image_downloader import ImageDownloader
from database import PinterestDatabase
import json

class PinterestScraperWithImages:
    def __init__(self, download_images: bool = True, headless: bool = True):
        self.scraper = PinterestScraper(headless=headless)
        self.database = PinterestDatabase()
        self.download_images = download_images
        
        if self.download_images:
            self.image_downloader = ImageDownloader()
    
    def scrape_board_with_images(self, board_url: str, max_pins: int = 100) -> dict:
        """Scrape a Pinterest board and optionally download images"""
        print(f"Scraping board: {board_url}")
        print(f"Max pins: {max_pins}")
        print(f"Download images: {self.download_images}")
        
        # Scrape the board
        result = self.scraper.scrape_board(board_url, max_pins)
        
        if 'error' in result:
            print(f"❌ Scraping failed: {result['error']}")
            return result
        
        pins = result.get('pins', [])
        print(f"✅ Scraped {len(pins)} pins")
        
        # Save pins to database
        saved_count = 0
        for pin in pins:
            try:
                pin['board_url'] = board_url
                self.database.save_pin(pin)
                saved_count += 1
            except Exception as e:
                print(f"Warning: Could not save pin {pin.get('pin_id', 'unknown')}: {e}")
        
        print(f"✅ Saved {saved_count} pins to database")
        
        # Download images if requested
        download_results = {}
        if self.download_images and pins:
            print(f"📥 Starting image download for {len(pins)} pins...")
            download_results = self.image_downloader.download_pin_images(pins)
            print(f"✅ Downloaded {download_results.get('downloaded', 0)} images")
            print(f"❌ Failed to download {download_results.get('failed', 0)} images")
            print(f"🖼️  Created {download_results.get('thumbnails_created', 0)} thumbnails")
        
        # Return comprehensive results
        return {
            'board_url': board_url,
            'pins_scraped': len(pins),
            'pins_saved': saved_count,
            'download_results': download_results,
            'pins': pins
        }
    
    def download_existing_pins(self, limit: int = None):
        """Download images for pins that are already in the database"""
        print("📥 Downloading images for existing pins...")
        
        # Get pins from database
        all_pins = self.database.get_all_pins()
        
        if limit:
            all_pins = all_pins[:limit]
        
        print(f"Found {len(all_pins)} pins in database")
        
        if not self.download_images:
            print("❌ Image downloading is disabled")
            return
        
        # Download images
        download_results = self.image_downloader.download_pin_images(all_pins)
        
        print(f"✅ Downloaded {download_results.get('downloaded', 0)} images")
        print(f"❌ Failed to download {download_results.get('failed', 0)} images")
        print(f"🖼️  Created {download_results.get('thumbnails_created', 0)} thumbnails")
        
        return download_results
    
    def get_stats(self):
        """Get comprehensive statistics"""
        # Database stats
        all_pins = self.database.get_all_pins()
        
        # Image download stats
        image_stats = {}
        if self.download_images:
            image_stats = self.image_downloader.get_download_stats()
        
        return {
            'database': {
                'total_pins': len(all_pins),
                'unique_boards': len(set(pin.get('board_url', '') for pin in all_pins))
            },
            'images': image_stats
        }
    
    def close(self):
        """Clean up resources"""
        self.scraper.close()

def main():
    """Example usage of the enhanced scraper"""
    print("=== Pinterest Scraper with Image Download ===\n")
    
    # Load configuration
    try:
        with open('board_urls.json', 'r') as f:
            config = json.load(f)
            board_urls = config.get('board_urls', [])
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        return
    
    if not board_urls:
        print("❌ No board URLs found in configuration")
        return
    
    # Create scraper with image downloading enabled
    scraper = PinterestScraperWithImages(download_images=True, headless=True)
    
    try:
        # Test with first board URL (limited pins for testing)
        test_board = board_urls[0]
        print(f"🔍 Testing with board: {test_board}")
        
        # Scrape with limited pins for testing
        result = scraper.scrape_board_with_images(test_board, max_pins=5)
        
        print(f"\n📊 Results:")
        print(f"   Pins scraped: {result.get('pins_scraped', 0)}")
        print(f"   Pins saved: {result.get('pins_saved', 0)}")
        
        download_results = result.get('download_results', {})
        if download_results:
            print(f"   Images downloaded: {download_results.get('downloaded', 0)}")
            print(f"   Download failures: {download_results.get('failed', 0)}")
            print(f"   Thumbnails created: {download_results.get('thumbnails_created', 0)}")
        
        # Show overall stats
        stats = scraper.get_stats()
        print(f"\n📈 Overall Statistics:")
        print(f"   Total pins in database: {stats['database']['total_pins']}")
        print(f"   Unique boards: {stats['database']['unique_boards']}")
        
        if stats.get('images'):
            print(f"   Downloaded images: {stats['images'].get('total_images', 0)}")
            print(f"   Total size: {stats['images'].get('total_size_mb', 0)} MB")
            print(f"   Download directory: {stats['images'].get('download_directory', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Error during scraping: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        scraper.close()

if __name__ == "__main__":
    main()
