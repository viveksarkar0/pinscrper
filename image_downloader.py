#!/usr/bin/env python3
"""
Image downloader module for Pinterest scraper
Downloads and saves images from Pinterest pins
"""

import os
import requests
import hashlib
from urllib.parse import urlparse
from typing import Dict, Optional
import logging
from PIL import Image
import io

class ImageDownloader:
    def __init__(self, download_dir: str = "downloaded_images"):
        self.download_dir = download_dir
        self.setup_logging()
        self.create_download_directory()
        
        # Session for efficient downloading
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def setup_logging(self):
        """Setup logging for image downloader"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def create_download_directory(self):
        """Create download directory structure"""
        try:
            # Create main download directory
            os.makedirs(self.download_dir, exist_ok=True)
            
            # Create subdirectories for organization
            subdirs = ['pins', 'thumbnails', 'failed']
            for subdir in subdirs:
                os.makedirs(os.path.join(self.download_dir, subdir), exist_ok=True)
                
            self.logger.info(f"Download directory created: {self.download_dir}")
            
        except Exception as e:
            self.logger.error(f"Error creating download directory: {e}")
    
    def generate_filename(self, pin_id: str, image_url: str, title: str = None) -> str:
        """Generate a unique filename for the image"""
        try:
            # Parse URL to get file extension
            parsed_url = urlparse(image_url)
            path = parsed_url.path
            
            # Try to get extension from URL
            if '.' in path:
                extension = path.split('.')[-1].lower()
                # Validate extension
                if extension not in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                    extension = 'jpg'
            else:
                extension = 'jpg'
            
            # Create filename using pin_id and hash of URL
            url_hash = hashlib.md5(image_url.encode()).hexdigest()[:8]
            
            if title:
                # Clean title for filename
                clean_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                clean_title = clean_title[:50]  # Limit length
                filename = f"{pin_id}_{clean_title}_{url_hash}.{extension}"
            else:
                filename = f"{pin_id}_{url_hash}.{extension}"
            
            return filename
            
        except Exception as e:
            self.logger.warning(f"Error generating filename: {e}")
            return f"{pin_id}_{hashlib.md5(image_url.encode()).hexdigest()[:8]}.jpg"
    
    def download_image(self, pin_data: Dict) -> Optional[str]:
        """Download a single image from pin data"""
        try:
            image_url = pin_data.get('image_url')
            pin_id = pin_data.get('pin_id')
            title = pin_data.get('title')
            
            if not image_url or not pin_id:
                self.logger.warning("Missing image_url or pin_id in pin data")
                return None
            
            # Generate filename
            filename = self.generate_filename(pin_id, image_url, title)
            filepath = os.path.join(self.download_dir, 'pins', filename)
            
            # Check if file already exists
            if os.path.exists(filepath):
                self.logger.info(f"Image already exists: {filename}")
                return filepath
            
            # Download the image
            self.logger.info(f"Downloading image: {filename}")
            response = self.session.get(image_url, timeout=30, stream=True)
            response.raise_for_status()
            
            # Verify it's an image
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                self.logger.warning(f"URL doesn't point to an image: {image_url}")
                return None
            
            # Save the image
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Verify the downloaded image
            try:
                with Image.open(filepath) as img:
                    # Check image size and format
                    width, height = img.size
                    if width < 50 or height < 50:
                        self.logger.warning(f"Image too small: {width}x{height}")
                        os.remove(filepath)
                        return None
                    
                    self.logger.info(f"Successfully downloaded: {filename} ({width}x{height})")
                    return filepath
                    
            except Exception as e:
                self.logger.error(f"Invalid image file: {e}")
                if os.path.exists(filepath):
                    os.remove(filepath)
                return None
                
        except requests.RequestException as e:
            self.logger.error(f"Error downloading image {image_url}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error downloading image: {e}")
            return None
    
    def create_thumbnail(self, image_path: str, thumbnail_size: tuple = (300, 300)) -> Optional[str]:
        """Create a thumbnail of the downloaded image"""
        try:
            if not os.path.exists(image_path):
                return None
            
            # Generate thumbnail filename
            base_name = os.path.basename(image_path)
            name, ext = os.path.splitext(base_name)
            thumbnail_name = f"{name}_thumb{ext}"
            thumbnail_path = os.path.join(self.download_dir, 'thumbnails', thumbnail_name)
            
            # Check if thumbnail already exists
            if os.path.exists(thumbnail_path):
                return thumbnail_path
            
            # Create thumbnail
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Create thumbnail
                img.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)
                img.save(thumbnail_path, quality=85, optimize=True)
                
                self.logger.info(f"Created thumbnail: {thumbnail_name}")
                return thumbnail_path
                
        except Exception as e:
            self.logger.error(f"Error creating thumbnail: {e}")
            return None
    
    def download_pin_images(self, pins_data: list, create_thumbnails: bool = True) -> Dict:
        """Download images for multiple pins"""
        results = {
            'downloaded': 0,
            'failed': 0,
            'skipped': 0,
            'thumbnails_created': 0,
            'files': []
        }
        
        self.logger.info(f"Starting download of {len(pins_data)} images...")
        
        for i, pin_data in enumerate(pins_data, 1):
            try:
                self.logger.info(f"Processing pin {i}/{len(pins_data)}: {pin_data.get('pin_id', 'unknown')}")
                
                # Download main image
                image_path = self.download_image(pin_data)
                
                if image_path:
                    results['downloaded'] += 1
                    results['files'].append(image_path)
                    
                    # Create thumbnail if requested
                    if create_thumbnails:
                        thumbnail_path = self.create_thumbnail(image_path)
                        if thumbnail_path:
                            results['thumbnails_created'] += 1
                            results['files'].append(thumbnail_path)
                else:
                    results['failed'] += 1
                    
            except Exception as e:
                self.logger.error(f"Error processing pin {pin_data.get('pin_id', 'unknown')}: {e}")
                results['failed'] += 1
        
        self.logger.info(f"Download complete: {results['downloaded']} downloaded, {results['failed']} failed")
        return results
    
    def get_download_stats(self) -> Dict:
        """Get statistics about downloaded images"""
        try:
            pins_dir = os.path.join(self.download_dir, 'pins')
            thumbnails_dir = os.path.join(self.download_dir, 'thumbnails')
            
            pins_count = len([f for f in os.listdir(pins_dir) if os.path.isfile(os.path.join(pins_dir, f))])
            thumbnails_count = len([f for f in os.listdir(thumbnails_dir) if os.path.isfile(os.path.join(thumbnails_dir, f))])
            
            # Calculate total size
            total_size = 0
            for root, dirs, files in os.walk(self.download_dir):
                for file in files:
                    filepath = os.path.join(root, file)
                    total_size += os.path.getsize(filepath)
            
            return {
                'total_images': pins_count,
                'total_thumbnails': thumbnails_count,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'download_directory': self.download_dir
            }
            
        except Exception as e:
            self.logger.error(f"Error getting download stats: {e}")
            return {}
    
    def cleanup_failed_downloads(self):
        """Clean up any failed or corrupted downloads"""
        try:
            pins_dir = os.path.join(self.download_dir, 'pins')
            failed_count = 0
            
            for filename in os.listdir(pins_dir):
                filepath = os.path.join(pins_dir, filename)
                
                try:
                    # Check if file is a valid image
                    with Image.open(filepath) as img:
                        img.verify()
                except Exception:
                    # Move to failed directory
                    failed_dir = os.path.join(self.download_dir, 'failed')
                    failed_path = os.path.join(failed_dir, filename)
                    os.rename(filepath, failed_path)
                    failed_count += 1
                    self.logger.info(f"Moved corrupted file to failed: {filename}")
            
            self.logger.info(f"Cleanup complete: {failed_count} corrupted files moved")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

def main():
    """Test the image downloader"""
    downloader = ImageDownloader()
    
    # Test with mock data
    mock_pins = [
        {
            'pin_id': 'test_001',
            'image_url': 'https://i.pinimg.com/564x/example.jpg',
            'title': 'Test Fashion Pin'
        }
    ]
    
    results = downloader.download_pin_images(mock_pins)
    print(f"Download results: {results}")
    
    stats = downloader.get_download_stats()
    print(f"Download stats: {stats}")

if __name__ == "__main__":
    main()
