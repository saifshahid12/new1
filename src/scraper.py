from selenium.webdriver.common.action_chains import ActionChains
import time
import json
import random
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from src.utils import load_credentials
import zipfile
import tempfile
import os
import pyautogui
import math
import numpy as np


# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class LinkedInScraper:
    """
    LinkedInScraper is a Selenium-based tool for extracting posts from LinkedIn
    while mimicking human behavior to avoid bot detection.

    Features:
    - Human-like scrolling, typing, and mouse movements
    - Proxy support (authenticated and unauthenticated)
    - Post parsing with duplicate detection
    - Robust timestamp and URL extraction
    - Category-based filtering
    """
    CATEGORY_URL_MAP = {
        "Posts": "/search/content/",
        "Jobs": "/search/jobs/",
        "People": "/search/people/",
        "Companies": "/search/companies/"
    }

    # --- CONSTANTS: Extracted Magic XPath / CSS Selectors ---
    LOGIN_USERNAME_FIELD = (By.NAME, 'session_key')
    LOGIN_PASSWORD_FIELD = (By.NAME, 'session_password')
    LOGIN_SUBMIT_BUTTON = (By.XPATH, "//button[@type='submit']")
    SEARCH_INPUT_FIELD = (By.CSS_SELECTOR, 'input.search-global-typeahead__input')
    POST_CONTAINER = (By.XPATH, "//div[contains(@class, 'feed-shared-update-v2')]")
    POST_AUTHOR_NAME = (By.XPATH, ".//span[@dir='ltr']/span[@aria-hidden='true']")
    POST_TIMESTAMP = (By.XPATH, ".//a[contains(@class, 'update-components-header__actor-action')]")
    POST_TEXT_EXPAND_BUTTON = (By.XPATH, ".//button[contains(@aria-label, 'see more') or contains(text(), 'see more') or contains(text(), '…see more')]")
    POST_TEXT_CONTENT = (By.XPATH, ".//div[contains(@class, 'update-components-text')]//span[@dir='ltr']")
    POST_URL = (By.XPATH, ".//a[contains(@class, 'update-components-header__actor-action')]")

    # ==================================================================================

    def __init__(self, config, init_driver=True):
        
        # start give to information 
        self.config = config
        self.driver = None
        self.scraped_data = []

        # Load credentials
        self.username, self.password = load_credentials()

        # Assign search query and category from config
        self.search_query = config['scraper_settings'].get('search_query', '')
        self.category = config.get('category', 'Posts')  # Default to 'Posts'

        self._validate_config()

        if init_driver:
            self._setup_driver()

    # ===============================================================================
    

    def _validate_config(self):

        """Validates critical configuration parameters."""

        # loggig info
        logging.info("Validating configuration parameters...")

        #  use scraper setting from config
        if 'scraper_settings' not in self.config:
            raise ValueError("CRITICAL: Missing 'scraper_settings' in config")

        settings = self.config['scraper_settings']
        required_fields = ['base_url', 'search_query', 'scroll_limit']

        # use if condition when something is missing form scraper setting (config)
        for field in required_fields:
            if field not in settings:
                raise ValueError(f"Missing required field in scraper_settings: '{field}'")

        # get scroll limit from config 
        scroll_limit = settings.get('scroll_limit')
        if not isinstance(scroll_limit, int) or scroll_limit <= 0:
            raise ValueError(f"Invalid 'scroll_limit': Must be a positive integer. Found: {scroll_limit}")

        # if not username or password then raise error 
        if not self.username or not self.password:
            raise ValueError("LinkedIn credentials not loaded from .env file")

        # loging info when all config complete 
        logging.info("Configuration validation complete.")

    # ==============================================================================

    def _setup_driver(self):

        """Configures and initializes Selenium Chrome WebDriver with optional proxy support."""

        logging.info("Setting up Chrome WebDriver...")
        service = ChromeService(ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        # Proxy config
        proxy_config = self.config.get("proxy", {})
        if proxy_config.get("enabled") and proxy_config.get("host") and proxy_config.get("port"):
            options.add_argument(f"--proxy-server=http://{proxy_config['host']}:{proxy_config['port']}")

        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    # ================================================================================

    def close(self):

        """Safely quits the WebDriver."""

        # when all are work then safely quite 
        if self.driver:
            self.driver.quit()
            self.driver = None

            # logginginfo when broweser close 
            logging.info("Browser session closed.")

    # ===================================================================================

    def _random_delay(self, min_time: float = None, max_time: float = None):

        """Implements a human-like, random delay between actions."""

        # if min or max time not here 
        if min_time is None or max_time is None:
            
            # then get time from config file 
            settings = self.config['scraper_settings'].get('delay', {'min_sec': 1.0, 'max_sec': 3.0})
            min_sec = settings['min_sec']
            max_sec = settings['max_sec']

        else:
            min_sec, max_sec = min_time, max_time

        time.sleep(random.uniform(min_sec, max_sec))

    # =====================================================================================

    def login(self):

        """Automates the login process to LinkedIn with human-like typing and mouse movements."""
        # get url from config file 
        url = self.config['scraper_settings']['base_url']

        # after get url show ino about page 
        logging.info(f"Navigating to login page: {url}")

        # max_delay
        self.driver.get(url)
        self._random_delay(2, 3)

        try:
            # write code for username enter and delay
            wait = WebDriverWait(self.driver, 20)
            username_field = wait.until(EC.presence_of_element_located(self.LOGIN_USERNAME_FIELD))
            self._human_mouse_movement(3)
            self._human_typing(username_field, self.username)

            # logging informatio when username enter
            logging.info("Username entered.")
            self._random_delay(1, 2)

            # write code for password enter and delay
            password_field = wait.until(EC.presence_of_element_located(self.LOGIN_PASSWORD_FIELD))
            self._human_mouse_movement(2)
            self._human_typing(password_field, self.password)

            # logging information when password enter
            logging.info("Password entered.")
            self._random_delay(1, 2)

            # code of submitt button after username and password enter
            submit_button = wait.until(EC.element_to_be_clickable(self.LOGIN_SUBMIT_BUTTON))
            submit_button.click()

            # logging information of subbmit button 
            logging.info("Login credentials submitted. Waiting for navigation...")
            self._random_delay(5, 8)

            try:
                # after all of that give info to successful login
                wait.until(EC.presence_of_element_located(self.SEARCH_INPUT_FIELD))

                # logging info of succesfully enter user and pass 
                logging.info("Login successful - Search bar found.")
                self._human_presence()

            except TimeoutException:

                # if any problem or mistake occur in username or pass give info
                logging.warning("Login may have failed or encountered security check")

        except (NoSuchElementException, TimeoutException) as e:
            logging.error(f"Login failed: {e}")
            raise

    #================================================================================

    def perform_search(self):

        """Performs LinkedIn search for the configured query with proper waits."""

        # when login success then ready for search 
        logging.info(f"Executing search for query: '{self.search_query}'")

        try:
            # Wait until search input is present
            search_box = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//input[contains(@placeholder,'Search')]"))
            )

            # ready for searching box is ready 
            search_box.clear()
            search_box.send_keys(self.search_query)
            search_box.send_keys(Keys.ENTER)

            # logging info after search waiting for result 
            logging.info("Search submitted. Waiting for results page...")

            # Wait until at least one post container is loaded
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located(self.POST_CONTAINER)
            )

           

        except TimeoutException:

            # logging info if time or internet out then show error  
            logging.error("Search box or results page did not load in time.")

            raise
    
    # ================================================================================

            
    # =====================================================================================

    def human_like_scroll(self):

        """Simulates continuous scrolling down the page to load more posts."""
        try:
            # select scroll limit from config file 
            scroll_limit = self.config['scraper_settings']['scroll_limit']

            # select max scroll attempts from config 
            max_attempts = self.config['scraper_settings'].get('max_scroll_attempts', 50)

            # then return result of scrolling 
            last_height = self.driver.execute_script("return document.body.scrollHeight")

            # add how much time count scroll (mention in config)
            scroll_count = 0

            # add attempts how much time attempts (mention in config)
            attempts = 0

            # logging info when all is okay 
            logging.info(f"Starting human-like scrolling (limit: {scroll_limit})...")

            # use while loop for all scrolling process
            while scroll_count < scroll_limit and attempts < max_attempts:

                # use if condition like a human scroll 
                if random.random() < 0.3:
                    self._random_human_action()

                # use for random mouse move 
                self._random_human_mouse_move()
                self._random_delay(2, 3)
                self._human_presence()

                # random scroll time 
                scroll_by = random.randint(700, 1500)

                # when scroll start then use try method
                try:
                    self.driver.execute_script(f"window.scrollBy(0, {scroll_by});")
                except WebDriverException as e:

                    # logging info when not scroll 
                    logging.error(f"Scrolling failed: {e}")

                    # then stop 
                    break

                # Add random delay between scroling 
                self._random_delay(1.5, 3.5)

                # add for output of scrolling after perfect  work 
                try:
                    new_height = self.driver.execute_script("return document.body.scrollHeight")

                except WebDriverException as e:

                    #loging info if not scroll then show erroe 
                    logging.error(f"Error getting scroll height: {e}")

                    break

                # add now scroll posts to existing_post
                if new_height == last_height:
                    attempts += 1

                    # if posts not eqaual  to attempts time then show error 
                    if attempts % 5 == 0:

                        # logging warniing 
                        logging.warning(f"No new content loaded for {attempts} attempts.")

                    self._random_delay(2, 4)

                # if all are in good work then go to else and show informtion 
                else:
                    scroll_count += 1
                    attempts = 0
                    last_height = new_height

                    # logging information about scrolling and counting 
                    logging.info(f"Scrolled {scroll_count}/{scroll_limit} times.")

            # logging info after all work show finished 
            logging.info("Scrolling finished.")

            # if not working then showw error 
        except Exception as e:

            # logging error 
            logging.error(f"Scrolling error: {e}")

    # ===============================================================================


    def _parse_single_post(self, post_element) -> dict:

        """Parses a single LinkedIn post element into a structured dictionary."""

        # show data for all working elemnt which we use 
        post_data = {
            'Post Text': None,
            'Author Name': None,
            'Timestamp': None,
            'Post URL': None,
            'Category': getattr(self, 'category', 'Posts'),
            'Date_For_Sorting': None
        }

            
       
        # Expand post text  =====================================
        try:
            # Try multiple XPaths for "see more" button
            see_more_xpaths = [
                ".//button[contains(@aria-label, 'see more')]",
                ".//button[contains(text(), 'see more')]",
                ".//button[contains(text(), '…see more')]",
                ".//span[contains(text(), 'see more')]/ancestor::button"
            ]
            
            see_more_button = None
            for xpath in see_more_xpaths:
                try:
                    see_more_button = post_element.find_element(By.XPATH, xpath)
                    if see_more_button and see_more_button.is_displayed():
                        break
                except:
                    continue
            
            if see_more_button:
                self.driver.execute_script("arguments[0].click();", see_more_button)
                self._random_delay(0.5, 1.0)
                logging.debug("Clicked 'see more' button")
                
        except Exception as e:
            logging.debug(f"No 'see more' button found or already expanded: {e}")

        # Extract text ===========================================
        try:
            
            # use extract to text element from posts 
            text_element = post_element.find_element(*self.POST_TEXT_CONTENT)

            # data extract from just posts text 
            post_data['Post Text'] = " ".join(text_element.text.split()).strip()

        except NoSuchElementException:
            post_data['Post Text'] = "[No Text Content Found]"


        # Extract author =========================================
        try:
            # Try multiple selectors for author
            author_selectors = [
                ".//span[@dir='ltr']/span[@aria-hidden='true']",
                ".//span[contains(@class, 'update-components-actor__title')]//span[@aria-hidden='true']",
                ".//span[contains(@class, 'feed-shared-actor__name')]",
                ".//a[contains(@class, 'update-components-actor__name')]//span",
                ".//span[contains(@class, 'update-components-actor__name')]",
                ".//div[contains(@class, 'update-components-actor__title')]//span"
            ]
            
            author_found = False
            for selector in author_selectors:
                try:
                    author_element = post_element.find_element(By.XPATH, selector)
                    author_text = author_element.text.strip()
                    
                    # Filter out common non-author text
                    if author_text and author_text != "..." and len(author_text) > 1:
                        # Check if it's not a time indicator (like "2h", "3d")
                        time_indicators = ['h', 'd', 'w', 'm', 'ago', 'min', 'hour', 'day', 'week', 'month']
                        if not any(indicator in author_text.lower() for indicator in time_indicators):
                            post_data['Author Name'] = author_text
                            author_found = True
                            logging.debug(f"Author found via selector '{selector}': {author_text}")
                            break
                except:
                    continue
            
            # If no author found, try to get from image alt text
            if not author_found:
                try:
                    author_img = post_element.find_element(By.XPATH, ".//img[contains(@class, 'update-components-actor__avatar-image')]")
                    author_text = author_img.get_attribute("alt")
                    if author_text and "photo" not in author_text.lower():
                        post_data['Author Name'] = author_text.replace("photo", "").strip()
                        author_found = True
                        logging.debug(f"Author from alt text: {post_data['Author Name']}")
                except:
                    pass
            
            # If still no author, mark as unknown but don't log warning
            if not author_found:
                post_data['Author Name'] = "[Unknown Author]"
                logging.debug(f"No author found for post index")

        except NoSuchElementException:
            post_data['Author Name'] = "[Unknown Author]"
            logging.debug("Author element not found")


        # Extract timestamp =========================================
        try:
            timestamp = "[Unknown Time]"
            
            # Strategy 1: Try <time> tag
            try:
                time_elements = post_element.find_elements(By.TAG_NAME, "time")
                if time_elements:
                    logging.debug(f"Found {len(time_elements)} <time> elements")
                    for time_elem in time_elements:
                        dt = time_elem.get_attribute("datetime")
                        if dt:
                            timestamp = dt
                            logging.info(f"✓ Timestamp via datetime: {timestamp}")
                            break
                        
                        aria_label = time_elem.get_attribute("aria-label")
                        if aria_label:
                            timestamp = aria_label
                            logging.info(f"✓ Timestamp via aria-label: {timestamp}")
                            break
                        
                        text = time_elem.text.strip()
                        if text:
                            timestamp = text
                            logging.info(f"✓ Timestamp via time.text: {timestamp}")
                            break
            except Exception as e:
                logging.debug(f"Strategy 1 error: {e}")
            
            # Strategy 2: Look for ANY span in the post header area
            if timestamp == "[Unknown Time]":
                try:
                    # Get ALL spans from the header
                    header_spans = post_element.find_elements(By.XPATH, ".//div[contains(@class, 'update-components-actor') or contains(@class, 'feed-shared-actor')]//span")
                    
                    logging.debug(f"Found {len(header_spans)} spans in header area")
                    
                    for span in header_spans:
                        text = span.text.strip()
                        
                        # Look for common time indicators
                        if text and len(text) < 50 and any(indicator in text.lower() for indicator in 
                            ['ago', 'min', 'hour', 'day', 'week', 'month', 'h', 'd', 'w', 'm', 'now', 'edited']):
                            
                            # Additional validation - check if it matches time pattern
                            import re
                            if re.search(r'\d+\s*(min|hour|day|week|month|h|d|w|m)', text, re.IGNORECASE) or 'ago' in text.lower() or 'now' in text.lower():
                                timestamp = text
                                logging.info(f"✓ Timestamp via header span: {timestamp}")
                                break
                
                except Exception as e:
                    logging.debug(f"Strategy 2 error: {e}")
            
            # Strategy 3: Check data attributes
            if timestamp == "[Unknown Time]":
                try:
                    # Check if post element has data-urn or other attributes with date info
                    all_with_data = post_element.find_elements(By.XPATH, ".//*[@data-*]")
                    for elem in all_with_data[:10]:  # Check first 10
                        attrs = self.driver.execute_script('return arguments[0].attributes', elem)
                        for attr in attrs:
                            if 'time' in attr['name'].lower() or 'date' in attr['name'].lower():
                                val = attr['value']
                                if val:
                                    timestamp = val
                                    logging.info(f"✓ Timestamp via data attribute {attr['name']}: {timestamp}")
                                    break
                        if timestamp != "[Unknown Time]":
                            break
                except Exception as e:
                    logging.debug(f"Strategy 3 error: {e}")
            
            # Strategy 4: Look for text with numbers followed by time units
            if timestamp == "[Unknown Time]":
                try:
                    import re
                    # Get entire post element text
                    all_text = post_element.text
                    
                    # Pattern for timestamps: "2h", "3d", "1w", "45m", "2 hours ago", etc.
                    patterns = [
                        r'\d+\s*(?:seconds?|secs?|s)\s+ago',
                        r'\d+\s*(?:minutes?|mins?|m)\s+ago',
                        r'\d+\s*(?:hours?|hrs?|h)\s+ago',
                        r'\d+\s*(?:days?|d)\s+ago',
                        r'\d+\s*(?:weeks?|wks?|w)\s+ago',
                        r'\d+\s*(?:months?|mo)\s+ago',
                        r'\d+\s*(?:years?|yrs?|y)\s+ago',
                        r'\d+m\b',  # 33m
                        r'\d+h\b',  # 2h
                        r'\d+d\b',  # 3d
                        r'\d+w\b',  # 1w
                        r'just now',
                        r'now'
                    ]
                    
                    for pattern in patterns:
                        match = re.search(pattern, all_text, re.IGNORECASE)
                        if match:
                            timestamp = match.group(0)
                            logging.info(f"✓ Timestamp via regex on full text: {timestamp}")
                            break
                except Exception as e:
                    logging.debug(f"Strategy 4 error: {e}")
            
            # Strategy 5: Last resort - dump first few elements to see structure
            if timestamp == "[Unknown Time]":
                try:
                    logging.debug(f"=== Debugging post by {post_data.get('Author Name', 'Unknown')} ===")
                    logging.debug(f"Post text preview: {post_data.get('Post Text', '')[:100]}")
                    
                    # Get outer HTML of header to see structure
                    try:
                        header_elem = post_element.find_element(By.XPATH, ".//div[contains(@class, 'update-components-actor') or contains(@class, 'feed-shared-actor')]")
                        header_html = header_elem.get_attribute('outerHTML')[:500]  # First 500 chars
                        logging.debug(f"Header HTML: {header_html}")
                    except:
                        pass
                    
                except Exception as e:
                    logging.debug(f"Debug dump error: {e}")
            
            post_data['Timestamp'] = timestamp
            post_data['Date_For_Sorting'] = self._extract_date_for_sorting(timestamp)
            
            # Only log warning for posts with known authors
            if timestamp == "[Unknown Time]" and post_data.get('Author Name') != "[Unknown Author]":
                logging.warning(f"No timestamp found for post by {post_data.get('Author Name', 'Unknown')}")
            elif timestamp == "[Unknown Time]":
                logging.debug(f"No timestamp found for post by unknown author")
        
        except Exception as e:
            logging.error(f"Error extracting timestamp: {e}")
            post_data['Timestamp'] = "[Unknown Time]"
            post_data['Date_For_Sorting'] = None

        #  post URL ==============================================
        try:
            try:
                # try for url to get posts elememnt
                urn = post_element.get_attribute("data-urn")

                # use condition 
                if urn and "activity" in urn:
                    activity_id = urn.split(":")[-1]

                    # add url of linkedin 
                    post_data['Post URL'] = f"https://www.linkedin.com/feed/update/urn:li:activity:{activity_id}"
 
                else:
                    # if invalid then show warning 
                    raise Exception("No valid URN")

            except:

                try:
                    # use Xpath of getting posts element data
                    link_element = post_element.find_element(By.XPATH, ".//a[contains(@href,'/feed/update')]")
                    post_data['Post URL'] = link_element.get_attribute("href").split("?")[0]

                except:
                    # if url in posts or not in posts 
                    post_data['Post URL'] = "[No URL Found]"

        except Exception as e:
            logging.debug(f"URL extraction error: {e}")
            post_data['Post URL'] = "[No URL Found]"

        return post_data

    # =============================================================================

    def _is_duplicate(self, post_data: dict) -> bool:

        """Checks if a post is already scraped based on URL or text+author+timestamp."""

        # use condition for duplicate url 
        if post_data.get('Post URL') and post_data['Post URL'] != "[No URL Found]":

            # if existing and new url will be same then match url 
            for existing_post in self.scraped_data:
                if existing_post.get('Post URL') == post_data['Post URL']:
                    return True

            # if two same data posts then show just one        
            return False

        if not post_data.get('Post Text'):
            return False

        for existing_post in self.scraped_data:

            # if both posts are equal or author name are same bot or posts time same 
            if (existing_post.get('Post Text') == post_data.get('Post Text') and
                existing_post.get('Author Name') == post_data.get('Author Name') and
                existing_post.get('Timestamp') == post_data.get('Timestamp')):

                # then it willl be true 
                return True
        return False

    # ================================================================================

    def extract_post_elements(self):
        """Extracts posts from the loaded page and adds them to scraped_data."""
        
        logging.info("Starting post element extraction...")
        
        try:
            WebDriverWait(self.driver, 15).until(EC.presence_of_element_located(self.POST_CONTAINER))
            
        except TimeoutException:
            logging.warning("No post elements found. Check page content.")
            return []
        
        # Get all post elements
        post_elements = self.driver.find_elements(*self.POST_CONTAINER)
        logging.info(f"Found {len(post_elements)} potential post elements.")
        
        selected_category = getattr(self, "category", "Posts")
        
        # Filter duplicate post elements by data-urn FIRST
        unique_post_elements = []
        seen_urns = set()
        
        for element in post_elements:
            try:
                # Try to get unique identifier for post
                urn = element.get_attribute("data-urn")
                if urn:
                    if urn not in seen_urns:
                        seen_urns.add(urn)
                        unique_post_elements.append(element)
                    else:
                        logging.debug(f"Skipping duplicate element by data-urn: {urn}")
                        continue
                else:
                    # If no URN, use outerHTML hash as identifier
                    html_hash = hash(element.get_attribute('outerHTML')[:500])
                    if html_hash not in seen_urns:
                        seen_urns.add(html_hash)
                        unique_post_elements.append(element)
                    else:
                        logging.debug("Skipping duplicate element by HTML hash")
                        continue
                        
            except Exception as e:
                logging.debug(f"Error checking element uniqueness: {e}")
                unique_post_elements.append(element)
        
        logging.info(f"Unique post elements after filtering: {len(unique_post_elements)}")
        
        # Temporary storage to track processed posts
        processed_post_urls = set()
        processed_post_texts = set()
        
        # Import email extraction function
        from src.utils import extract_emails_from_text
        

        for i, post_element in enumerate(unique_post_elements):
            # if (i + 1) % 50 == 0:
                # logging.info(f"Progress: Processed {i + 1}/{len(unique_post_elements)} posts, found {len(self.scraped_data)} with emails")
    
            try:
                post_data = self._parse_single_post(post_element)
                
                # Skip posts with [Unknown Author] immediately
                if post_data.get('Author Name') == "[Unknown Author]":
                    logging.debug(f"Skipping post with Unknown Author (index {i})")
                    continue
                
                # Ensure Category key exists
                post_data['Category'] = post_data.get('Category', selected_category)
                
                # Remove duplicate lowercase 'category' key if exists
                if 'category' in post_data:
                    del post_data['category']
                
                # Filter posts by category
                if post_data['Category'].lower() != selected_category.lower():
                    continue
                
                # Check for duplicates using URL and text
                post_url = post_data.get('Post URL', '')
                post_text = post_data.get('Post Text', '')
                
                # Skip if no text or empty text
                if not post_text or post_text == "[No Text Content Found]" or post_text.strip() == "":
                    logging.debug(f"Skipping post with no text (index {i})")
                    continue
                
                # Skip if already processed by URL
                if post_url and post_url != "[No URL Found]":
                    if post_url in processed_post_urls:
                        logging.debug(f"Skipping duplicate post (URL): {post_url}")
                        continue
                    processed_post_urls.add(post_url)
                
                # Also check text to avoid duplicates
                text_hash = hash(post_text[:200])
                if text_hash in processed_post_texts:
                    logging.debug(f"Skipping duplicate post (text): {post_text[:80]}...")
                    continue
                processed_post_texts.add(text_hash)
                
                # ============================================================
                # **NEW: CHECK FOR EMAILS IN POST TEXT**
                # ============================================================
                emails = extract_emails_from_text(post_text)
                
                # Skip posts with NO emails
                if not emails:
                    logging.debug(f"Skipping post without email (index {i}) - Author: {post_data.get('Author Name')}")
                    continue
                
                # Add email information to post_data
                post_data['email'] = emails[0] if emails else "No email"
                post_data['email_count'] = len(emails)
                post_data['emails'] = emails
                
                logging.info(f"✓ Post has {len(emails)} email(s): {emails}")
                # ============================================================
                
                # Use existing duplicate check
                if post_data['Post Text'] and not self._is_duplicate(post_data):
                    self.scraped_data.append(post_data)
                    logging.info(f"✓ Post {i+1} added (with email): {post_data.get('Author Name', 'Unknown')} - {post_data.get('Timestamp', 'No time')}")
                    
            except Exception as e:
                logging.error(f"Error processing post {i+1}: {e}", exc_info=True)
                continue
        
        logging.info(f"Extraction complete. Total unique posts with emails: {len(self.scraped_data)}")
        return self.scraped_data
    # ===============================================================================

    # ---------------- HUMAN MIMICRY ----------------
    def _generate_bezier_curve(self, x0, y0, x1, y1, x2, y2, num_points=30):
        points = []
        for t in [i / (num_points - 1) for i in range(num_points)]:
            x = (1 - t)**2 * x0 + 2 * (1 - t) * t * x1 + t**2 * x2
            y = (1 - t)**2 * y0 + 2 * (1 - t) * t * y1 + t**2 * y2
            points.append((int(x), int(y)))
        return points

    # ===============================================================================

    def _human_mouse_movement(self, element=None, moves=1):

        try:
            # get human mimicry data from config file 
            human_cfg = self.config.get("human_mimicry", {})
            # if not get data from config then also mouve enable 
            if not human_cfg.get("enable_mouse_movement", True):
                return

            # use pyautogui fo movement 
            screen_width, screen_height = pyautogui.size()

            for _ in range(moves):

                # give location for movement of mouse on screen 
                if element and hasattr(element, 'location') and element.is_displayed():
                    loc = element.location
                    size = element.size
                    # use target of scren for the mouse movement 
                    target_x = loc['x'] + size['width']//2 + random.randint(-10, 10)
                    target_y = loc['y'] + size['height']//2 + random.randint(-10, 10)


                # use bezier for target of mouse move 
                else:
                    # give random target 
                    target_x = random.randint(100, screen_width-100)
                    target_y = random.randint(100, screen_height-100)
                
                # give current position to move using pyautogui 
                current_x, current_y = pyautogui.position()
                ctrl_x = (current_x + target_x)//2 + random.randint(-50, 50)
                ctrl_y = (current_y + target_y)//2 + random.randint(-50, 50)
                points = self._generate_bezier_curve(current_x, current_y, ctrl_x, ctrl_y, target_x, target_y,
                                                     num_points=random.randint(20, 40))
 
 
                # satrting movig To from area and give duration 
                for px, py in points:
                    pyautogui.moveTo(px, py, duration=random.uniform(0.002, 0.01))
                    time.sleep(random.uniform(0.001, 0.005))

                # random duration of movement of mouse 
                for _ in range(random.randint(1, 3)):
                    jitter_x = target_x + random.randint(-3, 3)
                    jitter_y = target_y + random.randint(-3, 3)
                    pyautogui.moveTo(jitter_x, jitter_y, duration=random.uniform(0.05, 0.1))

                # logging information if mouse move 
                logging.info("Mouse moved successfully")

        except Exception as e:
            # logging warning if mouse not move 
            logging.warning(f"Mouse movement failed: {e}")

    # ================================================================================

    def _random_human_action(self):

        # use random ovement of mouse still position
        choice = random.choice(["mouse", "jitter", "idle"])

        # use condition for mouse 
        if choice == "mouse":
            self._human_mouse_movement()

        # use continuous still place 
        elif choice == "jitter":
            self._continuous_mouse_jitter()

        # sleep time if muse , jitter not work then 
        else:
            time.sleep(random.uniform(0.5, 1.5))

    # ==================================================================================

    def _human_typing(self, element, text: str):

        # type like a human (metion speed in config file )
        min_delay, max_delay = self.config["human_mimicry"]["typing_speed"]
        element.clear()

        # character which we enter like userame password 
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(min_delay, max_delay))

        # give sleep time 
        time.sleep(random.uniform(0.5, 1.0))

    # ==================================================================================

    def _random_human_mouse_move(self):
        try:
            # random movement form x to y with duration 
            element = self.driver.find_element("tag name", "body")
            x_offset = random.randint(-20, 20) 
            y_offset = random.randint(-20, 20)

            # perfornace pf mouse movement 
            ActionChains(self.driver).move_to_element_with_offset(element, x_offset, y_offset).perform()
      
        except WebDriverException as e:
            # if movement not work then mouse skip
            logging.warning(f"Random mouse move skipped: {e}")

    # ==================================================================================

    def _continuous_mouse_jitter(self, duration: float = 1.5):
        # for continuos move on still place 
        end_time = time.time() + duration

        # use in while looop
        while time.time() < end_time:
            self._random_human_mouse_move()

            # use delay time 
            time.sleep(random.uniform(0.3, 0.6))

    # ====================================================================================

    def _human_presence(self):

        # give random human action 
        if random.random() < 0.6:
            self._random_human_action()

    # =====================================================================================

    # ---------------- PROXY EXTENSION ----------------
    def _create_proxy_extension(self, proxy_url, username=None, password=None):
        return "fake_proxy_extension.zip"

    # =====================================================================================

    def _build_search_url(self):

        # build url of lionkedin 
        base = "https://www.linkedin.com/search/"

        # category of choice , we can change from config 
        category_map = {
            "posts": "content",
            "people": "people",
            "jobs": "jobs",
            "companies": "companies"
        }

        # if category work then category , if not then posts by default 
        selected = self.category.lower() if hasattr(self, 'category') else 'posts'
        search_type = category_map.get(selected, "content")

        # return mention things 
        return f"{base}{search_type}/?keywords={self.search_query}"

    # =====================================================================================
 
    def clean_export_data(scraped_data: list[dict]):

        """Removes unwanted keys before export."""
        # use category if present 
        for post in scraped_data:
            if 'category' in post:  
                del post['category']

        # if not here then scraped data just show 
        return scraped_data

    # ========================================================================================

    def _extract_date_for_sorting(self, timestamp: str):
        """
        Extracts date from timestamp string for sorting purposes.
        
        Args:
            timestamp (str): Raw timestamp from LinkedIn
            
        Returns:
            datetime.datetime or None: Parsed date object for sorting
        """
        if not timestamp or timestamp == "[Unknown Time]":
            return None
        
        try:
            # Try parsing ISO format (datetime attribute)
            if "T" in timestamp and "-" in timestamp:
                from datetime import datetime

                # Example: "2024-03-15T10:30:00.000Z"

                date_str = timestamp.split("T")[0]
                return datetime.strptime(date_str, "%Y-%m-%d")
            
            # Try parsing relative time (e.g., "2 days ago", "1 week ago")
            elif "ago" in timestamp.lower():
                return self._parse_relative_date(timestamp)
            
            # Try other common formats
            else:
                # Remove "on " prefix if present
                clean_timestamp = timestamp.replace("on ", "")

                from datetime import datetime
                # Try multiple date formats
                for fmt in ["%b %d, %Y", "%d %b %Y", "%B %d, %Y", "%Y-%m-%d"]:
                    try:
                        return datetime.strptime(clean_timestamp, fmt)
                    except ValueError:
                        continue
                        
        except Exception as e:

            # logging info if date not extract or not work 
            logging.debug(f"Could not parse date '{timestamp}': {e}")
        
        return None

    # =========================================================================================


    def _parse_relative_date(self, relative_time: str):
        """
        Parses relative time strings like "2 days ago", "1 week ago" into datetime.
        
        Args:
            relative_time (str): Relative time string
            
        Returns:
            datetime.datetime: Estimated absolute date
        """
        from datetime import datetime, timedelta
        import re
        
        # Get current time
        now = datetime.now()
        
        # Match patterns like "2 days ago", "1 week ago", "3 hours ago"
        pattern = r'(\d+)\s+(day|week|hour|minute|month|year)s?\s+ago'
        match = re.search(pattern, relative_time.lower())
        
        if match:
            amount = int(match.group(1))
            unit = match.group(2)
            
            if unit == "day":
                return now - timedelta(days=amount)
            elif unit == "week":
                return now - timedelta(weeks=amount)
            elif unit == "month":
                return now - timedelta(days=30*amount)
            elif unit == "year":
                return now - timedelta(days=365*amount)
            elif unit == "hour":
                return now - timedelta(hours=amount)
            elif unit == "minute":
                return now - timedelta(minutes=amount)
        
        return None

    # ========================================================================================

    def sort_posts_by_date(self, posts: list, sort_order: str = "latest"):
        """
        Sorts posts based on date according to specified order.
        
        Args:
            posts (list): List of post dictionaries
            sort_order (str): "latest" (newest first), "oldest" (oldest first), or "none"
            
        Returns:
            list: Sorted list of posts
        """
        if sort_order.lower() == "none":
            return posts
        
        # Filter posts with valid dates
        posts_with_dates = []
        posts_without_dates = []
        
        for post in posts:

            if post.get('Date_For_Sorting'):
                posts_with_dates.append(post)

            else:
                posts_without_dates.append(post)
        
        # Sort posts with dates
        reverse_order = (sort_order.lower() == "latest")
        posts_with_dates.sort(
            key=lambda x: x['Date_For_Sorting'], 
            reverse=reverse_order
        )
        
        # Combine: sorted posts with dates first, then posts without dates
        return posts_with_dates + posts_without_dates

    # ===============================================================================

    def select_category_from_config(self):
        """Selects LinkedIn category (Posts, Jobs, People, Companies) based on config."""

        category = self.config["scraper_settings"].get("category", "Posts")
        logging.info(f"Selecting category from config: {category}")

        try:
            # Wait for page to load after search
            self._random_delay(5, 7)

            # Click category button using exact text match
            category_button = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, f"//button[contains(@class, 'search-reusables__filter-pill-button') and contains(., '{category}')]"))
            )

            self._human_mouse_movement(category_button, moves=2)
            self.driver.execute_script("arguments[0].click();", category_button)

            logging.info(f"Category selected successfully: {category}")
            self._random_delay(4, 6)

        except Exception as e:
            logging.warning(f"Could not select category '{category}': {e}")
            logging.warning("Trying alternative XPath...")
            
            try:
                # Alternative XPath
                category_button = WebDriverWait(self.driver, 15).until(
                    EC.element_to_be_clickable((By.XPATH, f"//button[.//span[text()='{category}']]"))
                )
                self.driver.execute_script("arguments[0].click();", category_button)
                logging.info(f"Category selected with alternative method: {category}")
                self._random_delay(4, 6)
            except Exception as e2:
                logging.error(f"Failed to select category with both methods: {e2}")

    # ==================================================================================

    def apply_all_filters(self):
        """
        Opens 'All filters' panel and applies Sort by and Date posted filters from config.
        
        Workflow:
            1. Click "All filters" button to open filter panel
            2. Select "Sort by" option based on category and config
               - Posts: "Latest" or "Top match"
               - Jobs: "Most recent" or "Most relevant"
               - People/Companies: Category-specific options
            3. Select "Date posted" option (Past 24 hours/week/month) based on config
            4. Click "Show results" button to apply filters
            5. Wait for page to reload with filtered results
        
        Config Dependencies:
            - scraper_settings.category: "Posts", "Jobs", "People", or "Companies"
            - scraper_settings.sort_by_date: "latest" or "oldest"
            - scraper_settings.time_filter: "past_24_hours", "past_week", "past_month", or "none"
        
        Raises:
            TimeoutException: If filter elements don't load within timeout
            NoSuchElementException: If expected filter options not found
        """
        try:
            logging.info("Opening 'All filters' panel...")
            
            # Scroll to top to ensure button is visible
            self.driver.execute_script("window.scrollTo(0, 0);")
            self._random_delay(2, 3)
            
            # Get category from config to determine correct sort options
            category = self.config["scraper_settings"].get("category", "Posts")
            logging.info(f"Category detected: {category}")
            
            # Step 1: Click "All filters" button with multiple strategies
            all_filters_button = None
            
            # Try multiple XPath strategies
            all_filters_xpaths = [
                "//button[contains(text(), 'All filters')]",
                "//button[contains(@aria-label, 'Show all filters')]",
                "//button[contains(., 'All filters')]",
                "//button[.//span[contains(text(), 'All filters')]]"
            ]
            
            for xpath in all_filters_xpaths:
                try:
                    all_filters_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, xpath))
                    )
                    if all_filters_button:
                        break
                except:
                    continue
            
            if not all_filters_button:
                logging.error("'All filters' button not found on page")
                return
            
            # Click the button
            self._human_mouse_movement(all_filters_button, moves=2)
            self.driver.execute_script("arguments[0].click();", all_filters_button)
            logging.info("'All filters' panel opened")
            
            # Wait for filter panel to fully load
            self._random_delay(4, 6)
            
            # Verify panel is open by checking for "Show results" button
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//button[contains(., 'Show') and contains(., 'result')]"))
                )
                logging.info("Filter panel confirmed open")
            except TimeoutException:
                logging.warning("Filter panel may not have opened properly")
            
            # =====================================================================
            # Step 2: Apply "Sort by" filter (Category-aware)
            # =====================================================================
            sort_order = self.config["scraper_settings"].get("sort_by_date", "latest")
            
            if sort_order.lower() != "none":
                logging.info(f"Applying Sort by: {sort_order} for category: {category}")
                
                # Map config value to LinkedIn's actual text based on category
                sort_text = self._get_sort_text_for_category(category, sort_order)
                
                logging.info(f"Sort text to select: '{sort_text}'")
                
                try:
                    # Multiple strategies to find and click sort option
                    sort_xpaths = [
                        f"//label[contains(., '{sort_text}')]",
                        f"//span[text()='{sort_text}']/ancestor::label",
                        f"//span[contains(text(), '{sort_text}')]/ancestor::label",
                        f"//input[@value='{sort_text.upper()}']/following-sibling::label",
                        f"//fieldset//label[contains(., '{sort_text}')]"
                    ]
                    
                    sort_clicked = False
                    for xpath in sort_xpaths:
                        try:
                            sort_element = self.driver.find_element(By.XPATH, xpath)
                            self._human_mouse_movement(sort_element, moves=1)
                            self.driver.execute_script("arguments[0].click();", sort_element)
                            logging.info(f"Sort by '{sort_text}' selected successfully")
                            sort_clicked = True
                            self._random_delay(1, 2)
                            break
                        except:
                            continue
                    
                    if not sort_clicked:
                        logging.warning(f"Could not select sort option '{sort_text}'")
                    
                except Exception as e:
                    logging.warning(f"Error selecting sort: {e}")
            
            # =====================================================================
            # Step 3: Apply "Date posted" filter
            # =====================================================================
            time_filter = self.config["scraper_settings"].get("time_filter", "none")
            
            if time_filter.lower() != "none":
                logging.info(f"Applying Date posted: {time_filter}")
                
                # Map config value to LinkedIn's actual text
                time_map = {
                    "past_hour": "Past 24 hours",
                    "past_24_hours": "Past 24 hours",
                    "past_week": "Past week",
                    "past_month": "Past month"
                }
                
                date_text = time_map.get(time_filter.lower(), "Past 24 hours")
                
                try:
                    # Multiple strategies to find and click date filter
                    date_xpaths = [
                        f"//label[contains(., '{date_text}')]",
                        f"//span[text()='{date_text}']/ancestor::label",
                        f"//span[contains(text(), '{date_text}')]/ancestor::label",
                        f"//fieldset//label[contains(., '{date_text}')]"
                    ]
                    
                    date_clicked = False
                    for xpath in date_xpaths:
                        try:
                            date_element = self.driver.find_element(By.XPATH, xpath)
                            self._human_mouse_movement(date_element, moves=1)
                            self.driver.execute_script("arguments[0].click();", date_element)
                            logging.info(f"Date posted '{date_text}' selected successfully")
                            date_clicked = True
                            self._random_delay(1, 2)
                            break
                        except:
                            continue
                    
                    if not date_clicked:
                        logging.warning(f"Could not select date filter '{date_text}'")
                    
                except Exception as e:
                    logging.warning(f"Error selecting date filter: {e}")
            
            # =====================================================================
            # Step 4: Click "Show results" button and wait for page reload
            # =====================================================================
            try:
                # Store current URL before clicking "Show results"
                current_url = self.driver.current_url
                logging.info(f"Current URL before applying filters: {current_url}")
                
                # Multiple XPath strategies for "Show results" button
                show_results_xpaths = [
                    "//button[contains(., 'Show') and contains(., 'result')]",
                    "//button[contains(text(), 'Show')]",
                    "//button[@type='submit' and contains(., 'Show')]",
                    "//button[.//span[contains(text(), 'Show')]]"
                ]
                
                show_results_button = None
                for xpath in show_results_xpaths:
                    try:
                        show_results_button = WebDriverWait(self.driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, xpath))
                        )
                        if show_results_button:
                            break
                    except:
                        continue
                
                if show_results_button:
                    self._human_mouse_movement(show_results_button, moves=1)
                    self.driver.execute_script("arguments[0].click();", show_results_button)
                    logging.info("Clicked 'Show results' button")
                    
                    # ============================================================
                    # CRITICAL: Wait for page to reload with filtered results
                    # ============================================================
                    
                    # Wait for URL to change (indicates page navigation)
                    try:
                        WebDriverWait(self.driver, 15).until(
                            lambda driver: driver.current_url != current_url
                        )
                        logging.info("Page URL changed - filters applied, page reloaded")
                    except TimeoutException:
                        logging.warning("URL did not change - filters may have been applied without page reload")
                    
                    # Wait for filter panel to close (indicates filter application complete)
                    self._random_delay(3, 5)
                    
                    # Wait for new results to load based on category
                    if category.lower() == "jobs":
                        # For Jobs, wait for job cards to load
                        try:
                            WebDriverWait(self.driver, 20).until(
                                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'jobs-search-results__list')]"))
                            )
                            logging.info("Jobs results list loaded")
                        except TimeoutException:
                            logging.warning("Jobs results list did not load - trying alternative selector")
                            try:
                                WebDriverWait(self.driver, 10).until(
                                    EC.presence_of_element_located((By.XPATH, "//ul[contains(@class, 'jobs-search-results__list')]//li"))
                                )
                                logging.info("Job list items found")
                            except TimeoutException:
                                logging.warning("Could not confirm jobs loaded")
                    
                    elif category.lower() == "posts":
                        # For Posts, wait for post containers
                        try:
                            WebDriverWait(self.driver, 20).until(
                                EC.presence_of_element_located(self.POST_CONTAINER)
                            )
                            logging.info("Posts loaded after filter")
                        except TimeoutException:
                            logging.warning("Posts did not load after filter")
                    
                    else:
                        # For People/Companies, wait for search results
                        try:
                            WebDriverWait(self.driver, 20).until(
                                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'search-results-container')]"))
                            )
                            logging.info(f"{category} results loaded")
                        except TimeoutException:
                            logging.warning(f"{category} results may not have loaded")
                    
                    # Final wait to ensure page is stable
                    self._random_delay(4, 6)
                    
                    # Scroll to top of results to prepare for scrolling
                    self.driver.execute_script("window.scrollTo(0, 0);")
                    self._random_delay(1, 2)
                    
                    new_url = self.driver.current_url
                    logging.info(f"New URL after filters: {new_url}")
                    logging.info("Filters applied successfully - page ready for scrolling")
                    
                else:
                    logging.error("'Show results' button not found")
                
            except Exception as e:
                logging.error(f"Could not click 'Show results' button: {e}")
        
        except Exception as e:
            logging.error(f"Error in apply_all_filters: {e}", exc_info=True)
            # Don't raise - allow scraping to continue even if filters fail
    
    # ===============================================================================
    
    def _get_sort_text_for_category(self, category: str, sort_order: str) -> str:
        """
        Returns the correct sort option text based on category and sort order.
        
        LinkedIn uses different sort terminology for different categories:
        - Posts: "Latest" vs "Top match"
        - Jobs: "Most recent" vs "Most relevant"
        - People: "Recently added" vs "Most relevant"
        - Companies: "Most recent" vs "Most relevant"
        
        Args:
            category (str): Category name (Posts, Jobs, People, Companies)
            sort_order (str): Sort order from config ("latest" or "oldest")
        
        Returns:
            str: LinkedIn's actual sort option text for the given category
        
        Example:
            >>> _get_sort_text_for_category("Jobs", "latest")
            "Most recent"
            >>> _get_sort_text_for_category("Posts", "latest")
            "Latest"
        """
        # Define category-specific sort text mappings
        sort_mappings = {
            "Posts": {
                "latest": "Latest",
                "oldest": "Top match"
            },
            "Jobs": {
                "latest": "Most recent",
                "oldest": "Most relevant"
            },
            "People": {
                "latest": "Recently added",
                "oldest": "Most relevant"
            },
            "Companies": {
                "latest": "Most recent",
                "oldest": "Most relevant"
            }
        }
        
        # Get category-specific mapping (default to Posts if not found)
        category_map = sort_mappings.get(category, sort_mappings["Posts"])
        
        # Get sort text (default to "latest" option if sort_order not found)
        sort_text = category_map.get(sort_order.lower(), category_map["latest"])
        
        return sort_text
    
    # ===============================================================================
