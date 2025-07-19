import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent
import time
import json
import re
import random
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
import logging

class PinterestScraper:
    def __init__(self, headless: bool = True, delay: int = 2):
        self.delay = delay
        self.ua = UserAgent()
        self.setup_logging()
        self.setup_driver(headless)
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('pinterest_scraper.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_driver(self, headless: bool):
        """Setup Chrome WebDriver with optimal settings"""
        chrome_options = Options()
        
        if headless:
            chrome_options.add_argument("--headless")
        
        # Basic stability options
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Memory and performance options
        chrome_options.add_argument("--memory-pressure-off")
        chrome_options.add_argument("--max_old_space_size=4096")
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-renderer-backgrounding")
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")
        
        # Anti-detection options
        chrome_options.add_argument(f"--user-agent={self.ua.random}")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Logging options to reduce noise
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument("--silent")
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            # Install and setup ChromeDriver with retry logic
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Set timeouts
            self.driver.implicitly_wait(10)
            self.driver.set_page_load_timeout(30)
            
            # Execute script to remove webdriver property
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.logger.info("ChromeDriver setup successful")
            
        except Exception as e:
            self.logger.error(f"Failed to setup ChromeDriver: {e}")
            raise
    
    def extract_board_id_from_url(self, board_url: str) -> Optional[str]:
        """Extract board ID from Pinterest board URL"""
        try:
            # Pinterest board URLs typically follow: https://www.pinterest.com/username/board-name/
            pattern = r'pinterest\.com/([^/]+)/([^/]+)/?'
            match = re.search(pattern, board_url)
            if match:
                username, board_name = match.groups()
                return f"{username}/{board_name}"
            return None
        except Exception as e:
            self.logger.error(f"Error extracting board ID from URL {board_url}: {e}")
            return None
    
    def scroll_and_load_pins(self, max_pins: int = 1000) -> List[Dict]:
        """Scroll through the page and collect pin data"""
        pins_data = []
        seen_pins = set()
        scroll_attempts = 0
        max_scroll_attempts = 30  # Reduced from 50 to avoid over-scrolling
        consecutive_no_new_pins = 0
        max_consecutive_no_new = 3  # Stop if no new pins found for 3 attempts
        
        self.logger.info(f"Starting to collect pins (max: {max_pins})")
        
        while len(pins_data) < max_pins and scroll_attempts < max_scroll_attempts:
            try:
                # Wait for pins to load
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[data-test-id='pin']"))
                )
                
                # Find all pin elements - focus on board pins only
                pin_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-test-id='pin']")
                
                # Track pins before this scroll
                pins_before_scroll = len(pins_data)
                
                for pin_element in pin_elements:
                    if len(pins_data) >= max_pins:
                        break
                    
                    try:
                        # Check if this pin is part of the board (not a recommendation)
                        if not self.is_board_pin(pin_element):
                            continue
                            
                        pin_data = self.extract_pin_data(pin_element)
                        if pin_data and pin_data['pin_id'] not in seen_pins:
                            pins_data.append(pin_data)
                            seen_pins.add(pin_data['pin_id'])
                            
                            if len(pins_data) % 25 == 0:  # Report every 25 pins
                                self.logger.info(f"Collected {len(pins_data)} pins so far...")
                    
                    except Exception as e:
                        self.logger.warning(f"Error extracting pin data: {e}")
                        continue
                
                # Check if we found new pins in this scroll
                pins_after_scroll = len(pins_data)
                if pins_after_scroll == pins_before_scroll:
                    consecutive_no_new_pins += 1
                    self.logger.info(f"No new pins found in scroll attempt {scroll_attempts + 1}")
                else:
                    consecutive_no_new_pins = 0
                
                # Stop if we haven't found new pins for several attempts
                if consecutive_no_new_pins >= max_consecutive_no_new:
                    self.logger.info("No new pins found for multiple scroll attempts - likely reached end of board")
                    break
                
                # Check if we've reached recommendations section
                if self.has_reached_recommendations():
                    self.logger.info("Reached recommendations section - stopping collection")
                    break
                
                # Scroll down to load more pins
                current_height = self.driver.execute_script("return document.body.scrollHeight")
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(1, 10))  # Random delay between 1-10 seconds
                
                # Wait for new content to load
                time.sleep(2)
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                
                scroll_attempts += 1
                
                # If page height didn't change, we might be at the end
                if current_height == new_height:
                    consecutive_no_new_pins += 1
                    if consecutive_no_new_pins >= 2:
                        self.logger.info("Page height unchanged - reached end of content")
                        break
                    
            except Exception as e:
                self.logger.error(f"Error during scrolling: {e}")
                scroll_attempts += 1
                time.sleep(self.delay)
        
        self.logger.info(f"Collected {len(pins_data)} pins total")
        return pins_data
    
    def extract_pin_data(self, pin_element) -> Optional[Dict]:
        """Extract data from a single pin element"""
        try:
            pin_data = {}
            
            # Get pin URL and ID
            pin_link = pin_element.find_element(By.CSS_SELECTOR, "a[href*='/pin/']")
            pin_url = pin_link.get_attribute('href')
            pin_data['pin_url'] = pin_url
            
            # Extract pin ID from URL
            pin_id_match = re.search(r'/pin/(\d+)/', pin_url)
            if pin_id_match:
                pin_data['pin_id'] = pin_id_match.group(1)
            else:
                return None
            
            # Get image URL
            try:
                img_element = pin_element.find_element(By.CSS_SELECTOR, "img")
                image_url = img_element.get_attribute('src')
                if image_url:
                    pin_data['image_url'] = image_url
            except:
                pin_data['image_url'] = None
            
            # Get title/alt text
            try:
                img_element = pin_element.find_element(By.CSS_SELECTOR, "img")
                title = img_element.get_attribute('alt') or img_element.get_attribute('title')
                pin_data['title'] = title
            except:
                pin_data['title'] = None
            
            # Try to get description (may not always be available)
            try:
                desc_element = pin_element.find_element(By.CSS_SELECTOR, "[data-test-id='pin-description']")
                pin_data['description'] = desc_element.text
            except:
                pin_data['description'] = None
            
            return pin_data
            
        except Exception as e:
            self.logger.warning(f"Error extracting pin data: {e}")
            return None
    
    def is_board_pin(self, pin_element) -> bool:
        """Check if a pin element belongs to the board (not a recommendation)"""
        try:
            # Look for parent containers that indicate recommendations
            parent = pin_element
            for _ in range(5):  # Check up to 5 parent levels
                if parent is None:
                    break
                
                # Check for recommendation section indicators
                parent_classes = parent.get_attribute('class') or ''
                parent_data_testid = parent.get_attribute('data-test-id') or ''
                
                # Common indicators of recommendation sections
                recommendation_indicators = [
                    'more-ideas',
                    'more-like-this',
                    'recommendations',
                    'related-pins',
                    'similar-pins',
                    'explore-more'
                ]
                
                for indicator in recommendation_indicators:
                    if indicator in parent_classes.lower() or indicator in parent_data_testid.lower():
                        return False
                
                # Check for text content that indicates recommendations
                try:
                    parent_text = parent.text.lower()
                    if any(phrase in parent_text for phrase in ['more ideas', 'more like this', 'explore related']):
                        return False
                except:
                    pass
                
                parent = parent.find_element(By.XPATH, '..')
            
            return True
            
        except Exception as e:
            # If we can't determine, assume it's a board pin
            return True
    
    def has_reached_recommendations(self) -> bool:
        """Check if we've scrolled to the recommendations section"""
        try:
            # Look for common recommendation section headers
            recommendation_headers = [
                "More ideas for you",
                "More like this",
                "Explore related ideas",
                "More to explore",
                "Related ideas"
            ]
            
            # Check for these headers in the current viewport
            for header_text in recommendation_headers:
                try:
                    elements = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{header_text}')]")
                    if elements:
                        # Check if any of these elements are visible
                        for element in elements:
                            if element.is_displayed():
                                return True
                except:
                    continue
            
            # Also check for specific CSS selectors that indicate recommendations
            recommendation_selectors = [
                "[data-test-id*='more-ideas']",
                "[data-test-id*='related']",
                ".moreLikeThis",
                ".recommendations"
            ]
            
            for selector in recommendation_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements and any(el.is_displayed() for el in elements):
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            self.logger.warning(f"Error checking for recommendations section: {e}")
            return False
    
    def scrape_board(self, board_url: str, max_pins: int = 1000) -> Dict:
        """Scrape all pins from a Pinterest board"""
        self.logger.info(f"Starting to scrape board: {board_url}")
        
        try:
            # Navigate to the board
            self.driver.get(board_url)
            time.sleep(3)
            
            # Wait for the page to load
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-test-id='pin']"))
            )
            
            # Get board information
            board_info = self.extract_board_info()
            
            # Collect all pins
            pins_data = self.scroll_and_load_pins(max_pins)
            
            result = {
                'board_url': board_url,
                'board_info': board_info,
                'pins': pins_data,
                'total_pins_scraped': len(pins_data)
            }
            
            self.logger.info(f"Successfully scraped {len(pins_data)} pins from board")
            return result
            
        except Exception as e:
            self.logger.error(f"Error scraping board {board_url}: {e}")
            return {
                'board_url': board_url,
                'board_info': {},
                'pins': [],
                'total_pins_scraped': 0,
                'error': str(e)
            }
    
    def extract_board_info(self) -> Dict:
        """Extract board title and description"""
        board_info = {}
        
        try:
            # Try to get board title
            title_selectors = [
                "h1[data-test-id='board-name']",
                "h1",
                "[data-test-id='board-name']"
            ]
            
            for selector in title_selectors:
                try:
                    title_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    board_info['title'] = title_element.text
                    break
                except:
                    continue
            
            # Try to get board description
            desc_selectors = [
                "[data-test-id='board-description']",
                ".board-description",
                ".boardDescription"
            ]
            
            for selector in desc_selectors:
                try:
                    desc_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    board_info['description'] = desc_element.text
                    break
                except:
                    continue
                    
        except Exception as e:
            self.logger.warning(f"Error extracting board info: {e}")
        
        return board_info
    
    def scrape_multiple_boards(self, board_urls: List[str], max_pins_per_board: int = 1000) -> List[Dict]:
        """Scrape multiple Pinterest boards"""
        results = []
        
        for i, board_url in enumerate(board_urls, 1):
            self.logger.info(f"Scraping board {i}/{len(board_urls)}: {board_url}")
            
            try:
                result = self.scrape_board(board_url, max_pins_per_board)
                results.append(result)
                
                # Add delay between boards to avoid rate limiting
                if i < len(board_urls):
                    time.sleep(self.delay * 2)
                    
            except Exception as e:
                self.logger.error(f"Failed to scrape board {board_url}: {e}")
                results.append({
                    'board_url': board_url,
                    'board_info': {},
                    'pins': [],
                    'total_pins_scraped': 0,
                    'error': str(e)
                })
        
        return results
    
    def close(self):
        """Close the WebDriver"""
        if hasattr(self, 'driver'):
            self.driver.quit()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
