#!/usr/bin/env python3
"""
Pinterest authentication helper for the scraper
"""

import os
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv

load_dotenv()

class PinterestAuth:
    def __init__(self, driver):
        self.driver = driver
        self.email = os.getenv('PINTEREST_EMAIL')
        self.password = os.getenv('PINTEREST_PASSWORD')
    
    def login(self):
        """Login to Pinterest"""
        if not self.email or not self.password:
            print("⚠️  Pinterest credentials not found in .env file")
            print("Please add PINTEREST_EMAIL and PINTEREST_PASSWORD to your .env file")
            return False
        
        try:
            print("Attempting to login to Pinterest...")
            
            # Go to Pinterest login page
            self.driver.get("https://www.pinterest.com/login/")
            time.sleep(3)
            
            # Find and fill email field
            email_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "email"))
            )
            email_field.clear()
            email_field.send_keys(self.email)
            
            # Find and fill password field
            password_field = self.driver.find_element(By.ID, "password")
            password_field.clear()
            password_field.send_keys(self.password)
            
            # Click login button
            login_button = self.driver.find_element(By.CSS_SELECTOR, "[data-test-id='registerFormSubmitButton']")
            login_button.click()
            
            # Wait for login to complete
            time.sleep(5)
            
            # Check if login was successful
            current_url = self.driver.current_url
            if "login" not in current_url.lower():
                print("✓ Successfully logged in to Pinterest")
                return True
            else:
                print("✗ Login failed - still on login page")
                return False
                
        except Exception as e:
            print(f"✗ Login failed: {e}")
            return False
    
    def check_login_status(self):
        """Check if we're currently logged in"""
        try:
            # Look for elements that indicate we're logged in
            profile_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-test-id='header-profile']")
            if profile_elements:
                return True
            
            # Check if we're on a page that requires login
            page_source = self.driver.page_source.lower()
            if "sign up" in page_source or "log in" in page_source:
                return False
            
            return True
            
        except Exception as e:
            print(f"Error checking login status: {e}")
            return False
    
    def handle_signup_prompt(self):
        """Handle signup prompts that might appear"""
        try:
            # Look for and close any signup modals
            close_buttons = self.driver.find_elements(By.CSS_SELECTOR, "[aria-label='Close'], .close, [data-test-id='closeButton']")
            for button in close_buttons:
                try:
                    if button.is_displayed():
                        button.click()
                        time.sleep(1)
                        print("✓ Closed signup prompt")
                        return True
                except:
                    continue
            
            # Try pressing Escape key
            from selenium.webdriver.common.keys import Keys
            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            time.sleep(1)
            
            return True
            
        except Exception as e:
            print(f"Error handling signup prompt: {e}")
            return False
