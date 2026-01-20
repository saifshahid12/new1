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
    POST_TEXT_EXPAND_BUTTON = (By.XPATH, ".//button[text()[contains(., '...see more')]]")
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
            # use .find element for posts 
            see_more_button = post_element.find_element(*self.POST_TEXT_EXPAND_BUTTON)

            # add argumemts click () when script execute 
            self.driver.execute_script("arguments[0].click();", see_more_button)

            # delay between  find element 
            self._random_delay(0.3, 0.6)

        except NoSuchElementException:


            pass


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
                ".//a[contains(@class, 'update-components-actor__name')]//span"
            ]
            
            for selector in author_selectors:
                try:
                    # use or author from posts by Xpath
                    author_element = post_element.find_element(By.XPATH, selector)
                    author_text = author_element.text.strip()

                    # use condition for author 
                    if author_text and author_text != "...":
                        post_data['Author Name'] = author_text

                        break
                except:
                    continue
            
            # if Author name present then show name otherwise unknwn 
            if not post_data['Author Name']:
                post_data['Author Name'] = "[Unknown Author]"

        except NoSuchElementException:
            post_data['Author Name'] = "[Unknown Author]"


        # Extract timestamp =========================================
        try:
            
            # Multiple strategies to get timestamp
            timestamp = "[Unknown Time]"
            
            # Strategy 1: Try to find datetime attribute
            try:
                time_elements = post_element.find_elements(By.TAG_NAME, "time")
                for time_elem in time_elements:
                    dt = time_elem.get_attribute("datetime")
                    if dt:
                        timestamp = dt
                        break
                    else:
                        # Try aria-label
                        aria_label = time_elem.get_attribute("aria-label")
                        if aria_label:
                            timestamp = aria_label
                            break
                        # Try text
                        text = time_elem.text.strip()
                        if text:
                            timestamp = text
                            break
            except:
                pass
            
            # Strategy 2: Look for relative time text
            if timestamp == "[Unknown Time]":
                try:
                    # Common LinkedIn timestamp patterns
                    time_patterns = [
                        ".//span[contains(@class, 'update-components-actor__sub-description')]",
                        ".//span[contains(@class, 'feed-shared-actor__sub-description')]",
                        ".//span[contains(text(), 'ago')]",
                        ".//span[contains(text(), 'day')]",
                        ".//span[contains(text(), 'week')]",
                        ".//span[contains(text(), 'month')]",
                        ".//span[contains(text(), 'hour')]",
                        ".//span[contains(text(), 'minute')]"
                    ]
                    
                    for pattern in time_patterns:
                        try:
                            time_elem = post_element.find_element(By.XPATH, pattern)
                            time_text = time_elem.text.strip()
                            if time_text and len(time_text) < 50:  # Reasonable length
                                timestamp = time_text
                                break
                        except:
                            continue
                except:
                    pass
            
            post_data['Timestamp'] = timestamp
            
            # Extract date for sorting
            post_data['Date_For_Sorting'] = self._extract_date_for_sorting(timestamp)
        
        
        except Exception as e:
            logging.debug(f"Error extracting error: {e}")
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

        # logging information when extraction start 
        logging.info("Starting post element extraction...")

        # use try for delay for the next posts extraction 
        try:
            WebDriverWait(self.driver, 15).until(EC.presence_of_element_located(self.POST_CONTAINER))

        # if no extraction then show logging warning
        except TimeoutException:
            logging.warning("No post elements found. Check page content.")

            return []

        # for posts element extracton 
        post_elements = self.driver.find_elements(*self.POST_CONTAINER)

        # loging information when extraction complete
        logging.info(f"Found {len(post_elements)} potential post elements.")

        # now selection of category (mention in config file )
        selected_category = getattr(self, "category", "Posts")

        # start element extraction 0 to 50 
        for i, post_element in enumerate(post_elements[:50]):

            try:
                post_data = self._parse_single_post(post_element)

                # Ensure Category key exists
                post_data['Category'] = post_data.get('Category', selected_category)

                # Remove duplicate lowercase 'category' key if exists
                if 'category' in post_data:
                    del post_data['category']

                # Filter posts by category
                if post_data['Category'].lower() != selected_category.lower():
                    continue
                
                # use condition for duplicate posts data 
                if post_data['Post Text'] and not self._is_duplicate(post_data):
                    self.scraped_data.append(post_data)

                    # logging information of getting posts data 
                    logging.debug(f"Post {i+1} added: {post_data.get('Author Name', 'Unknown')}")
            except Exception as e:
                # if not post data get then show warning 
                logging.error(f"Error processing post {i+1}: {e}")
                continue
        
        # if all are working then ending info 
        logging.info(f"Extraction complete. Total unique posts: {len(self.scraped_data)}")

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