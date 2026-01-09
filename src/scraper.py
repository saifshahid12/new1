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

    def __init__(self, config, init_driver=True):
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
        logging.info("Validating configuration parameters...")

        if 'scraper_settings' not in self.config:
            raise ValueError("CRITICAL: Missing 'scraper_settings' in config")

        settings = self.config['scraper_settings']
        required_fields = ['base_url', 'search_query', 'scroll_limit']
        for field in required_fields:
            if field not in settings:
                raise ValueError(f"Missing required field in scraper_settings: '{field}'")

        scroll_limit = settings.get('scroll_limit')
        if not isinstance(scroll_limit, int) or scroll_limit <= 0:
            raise ValueError(f"Invalid 'scroll_limit': Must be a positive integer. Found: {scroll_limit}")

        if not self.username or not self.password:
            raise ValueError("LinkedIn credentials not loaded from .env file")

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
        if self.driver:
            self.driver.quit()
            self.driver = None
            logging.info("Browser session closed.")

    # ===================================================================================

    def _random_delay(self, min_time: float = None, max_time: float = None):
        """Implements a human-like, random delay between actions."""
        if min_time is None or max_time is None:
            settings = self.config['scraper_settings'].get('delay', {'min_sec': 1.0, 'max_sec': 3.0})
            min_sec = settings['min_sec']
            max_sec = settings['max_sec']
        else:
            min_sec, max_sec = min_time, max_time

        time.sleep(random.uniform(min_sec, max_sec))

    # =====================================================================================

    def login(self):
        """Automates the login process to LinkedIn with human-like typing and mouse movements."""
        url = self.config['scraper_settings']['base_url']
        logging.info(f"Navigating to login page: {url}")
        self.driver.get(url)
        self._random_delay(2, 3)

        try:
            wait = WebDriverWait(self.driver, 20)
            username_field = wait.until(EC.presence_of_element_located(self.LOGIN_USERNAME_FIELD))
            self._human_mouse_movement(3)
            self._human_typing(username_field, self.username)
            logging.info("Username entered.")
            self._random_delay(1, 2)

            password_field = wait.until(EC.presence_of_element_located(self.LOGIN_PASSWORD_FIELD))
            self._human_mouse_movement(2)
            self._human_typing(password_field, self.password)
            logging.info("Password entered.")
            self._random_delay(1, 2)

            submit_button = wait.until(EC.element_to_be_clickable(self.LOGIN_SUBMIT_BUTTON))
            submit_button.click()
            logging.info("Login credentials submitted. Waiting for navigation...")
            self._random_delay(5, 8)

            try:
                wait.until(EC.presence_of_element_located(self.SEARCH_INPUT_FIELD))
                logging.info("Login successful - Search bar found.")
                self._human_presence()
            except TimeoutException:
                logging.warning("Login may have failed or encountered security check")
        except (NoSuchElementException, TimeoutException) as e:
            logging.error(f"Login failed: {e}")
            raise

    #================================================================================

    def perform_search(self):
        """Performs LinkedIn search for the configured query with proper waits."""
        logging.info(f"Executing search for query: '{self.search_query}'")
        try:
            # Wait until search input is present
            search_box = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//input[contains(@placeholder,'Search')]"))
            )
            search_box.clear()
            search_box.send_keys(self.search_query)
            search_box.send_keys(Keys.ENTER)
            logging.info("Search submitted. Waiting for results page...")

            # Wait until at least one post container is loaded
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located(self.POST_CONTAINER)
            )
        except TimeoutException:
            logging.error("Search box or results page did not load in time.")
            raise
    
    # ================================================================================

    def human_like_scroll(self):
        """Simulates continuous scrolling down the page to load more posts."""
        try:
            scroll_limit = self.config['scraper_settings']['scroll_limit']
            max_attempts = self.config['scraper_settings'].get('max_scroll_attempts', 50)
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            scroll_count = 0
            attempts = 0
            logging.info(f"Starting human-like scrolling (limit: {scroll_limit})...")

            while scroll_count < scroll_limit and attempts < max_attempts:
                if random.random() < 0.3:
                    self._random_human_action()
                self._random_human_mouse_move()
                self._random_delay(2, 3)
                self._human_presence()
                scroll_by = random.randint(700, 1500)
                try:
                    self.driver.execute_script(f"window.scrollBy(0, {scroll_by});")
                except WebDriverException as e:
                    logging.error(f"Scrolling failed: {e}")
                    break
                self._random_delay(1.5, 3.5)
                try:
                    new_height = self.driver.execute_script("return document.body.scrollHeight")
                except WebDriverException as e:
                    logging.error(f"Error getting scroll height: {e}")
                    break
                if new_height == last_height:
                    attempts += 1
                    if attempts % 5 == 0:
                        logging.warning(f"No new content loaded for {attempts} attempts.")
                    self._random_delay(2, 4)
                else:
                    scroll_count += 1
                    attempts = 0
                    last_height = new_height
                    logging.info(f"Scrolled {scroll_count}/{scroll_limit} times.")
            logging.info("Scrolling finished.")
        except Exception as e:
            logging.error(f"Scrolling error: {e}")

    # ===============================================================================

    # ---------------- POST PARSING ----------------

    def _parse_single_post(self, post_element) -> dict:
        """Parses a single LinkedIn post element into a structured dictionary."""
        post_data = {
            'Post Text': None,
            'Author Name': None,
            'Timestamp': None,
            'Post URL': None,
            'Category': getattr(self, 'category', 'Posts')  # Single Category key
        }

        # Expand post text
        try:
            see_more_button = post_element.find_element(*self.POST_TEXT_EXPAND_BUTTON)
            self.driver.execute_script("arguments[0].click();", see_more_button)
            self._random_delay(0.3, 0.6)
        except NoSuchElementException:
            pass

        # Extract text
        try:
            text_element = post_element.find_element(*self.POST_TEXT_CONTENT)
            post_data['Post Text'] = " ".join(text_element.text.split()).strip()
        except NoSuchElementException:
            post_data['Post Text'] = "[No Text Content Found]"

        # Extract author
        try:
            author_element = post_element.find_element(*self.POST_AUTHOR_NAME)
            post_data['Author Name'] = author_element.text.strip()
        except NoSuchElementException:
            post_data['Author Name'] = "[Unknown Author]"

        # Extract timestamp
        try:
            time_tag = post_element.find_element(By.TAG_NAME, "time")
            post_data['Timestamp'] = (
                time_tag.get_attribute("datetime")
                or time_tag.get_attribute("aria-label")
                or time_tag.text.strip()
            )
        except NoSuchElementException:
            post_data['Timestamp'] = "[Unknown Time]"

        # Extract post URL
        try:
            urn = post_element.get_attribute("data-urn")
            if urn and "activity" in urn:
                activity_id = urn.split(":")[-1]
                post_data['Post URL'] = f"https://www.linkedin.com/feed/update/urn:li:activity:{activity_id}"
            else:
                raise NoSuchElementException
        except Exception:
            try:
                link_element = post_element.find_element(By.XPATH, ".//a[contains(@href,'/feed/update')]")
                post_data['Post URL'] = link_element.get_attribute("href").split("?")[0]
            except NoSuchElementException:
                post_data['Post URL'] = "[No URL Found]"

        return post_data

    # =============================================================================

    def _is_duplicate(self, post_data: dict) -> bool:
        """Checks if a post is already scraped based on URL or text+author+timestamp."""
        if post_data.get('Post URL') and post_data['Post URL'] != "[No URL Found]":
            for existing_post in self.scraped_data:
                if existing_post.get('Post URL') == post_data['Post URL']:
                    return True
            return False
        if not post_data.get('Post Text'):
            return False
        for existing_post in self.scraped_data:
            if (existing_post.get('Post Text') == post_data.get('Post Text') and
                existing_post.get('Author Name') == post_data.get('Author Name') and
                existing_post.get('Timestamp') == post_data.get('Timestamp')):
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

        post_elements = self.driver.find_elements(*self.POST_CONTAINER)
        logging.info(f"Found {len(post_elements)} potential post elements.")

        selected_category = getattr(self, "category", "Posts")

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

                if post_data['Post Text'] and not self._is_duplicate(post_data):
                    self.scraped_data.append(post_data)
                    logging.debug(f"Post {i+1} added: {post_data.get('Author Name', 'Unknown')}")
            except Exception as e:
                logging.error(f"Error processing post {i+1}: {e}")
                continue

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
            human_cfg = self.config.get("human_mimicry", {})
            if not human_cfg.get("enable_mouse_movement", True):
                return
            screen_width, screen_height = pyautogui.size()
            for _ in range(moves):
                if element and hasattr(element, 'location') and element.is_displayed():
                    loc = element.location
                    size = element.size
                    target_x = loc['x'] + size['width']//2 + random.randint(-10, 10)
                    target_y = loc['y'] + size['height']//2 + random.randint(-10, 10)
                else:
                    target_x = random.randint(100, screen_width-100)
                    target_y = random.randint(100, screen_height-100)
                current_x, current_y = pyautogui.position()
                ctrl_x = (current_x + target_x)//2 + random.randint(-50, 50)
                ctrl_y = (current_y + target_y)//2 + random.randint(-50, 50)
                points = self._generate_bezier_curve(current_x, current_y, ctrl_x, ctrl_y, target_x, target_y,
                                                     num_points=random.randint(20, 40))
                for px, py in points:
                    pyautogui.moveTo(px, py, duration=random.uniform(0.002, 0.01))
                    time.sleep(random.uniform(0.001, 0.005))
                for _ in range(random.randint(1, 3)):
                    jitter_x = target_x + random.randint(-3, 3)
                    jitter_y = target_y + random.randint(-3, 3)
                    pyautogui.moveTo(jitter_x, jitter_y, duration=random.uniform(0.05, 0.1))
                logging.info("Mouse moved successfully")
        except Exception as e:
            logging.warning(f"Mouse movement failed: {e}")

    # ================================================================================

    def _random_human_action(self):
        choice = random.choice(["mouse", "jitter", "idle"])
        if choice == "mouse":
            self._human_mouse_movement()
        elif choice == "jitter":
            self._continuous_mouse_jitter()
        else:
            time.sleep(random.uniform(0.5, 1.5))

    # ==================================================================================

    def _human_typing(self, element, text: str):
        min_delay, max_delay = self.config["human_mimicry"]["typing_speed"]
        element.clear()
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(min_delay, max_delay))
        time.sleep(random.uniform(0.5, 1.0))

    # ==================================================================================

    def _random_human_mouse_move(self):
        try:
            element = self.driver.find_element("tag name", "body")
            x_offset = random.randint(-20, 20)
            y_offset = random.randint(-20, 20)
            ActionChains(self.driver).move_to_element_with_offset(element, x_offset, y_offset).perform()
        except WebDriverException as e:
            logging.warning(f"Random mouse move skipped: {e}")

    # ==================================================================================

    def _continuous_mouse_jitter(self, duration: float = 1.5):
        end_time = time.time() + duration
        while time.time() < end_time:
            self._random_human_mouse_move()
            time.sleep(random.uniform(0.3, 0.6))

    # ====================================================================================

    def _human_presence(self):
        if random.random() < 0.6:
            self._random_human_action()

    # =====================================================================================

    # ---------------- PROXY EXTENSION ----------------
    def _create_proxy_extension(self, proxy_url, username=None, password=None):
        return "fake_proxy_extension.zip"

    # =====================================================================================

    def _build_search_url(self):
        base = "https://www.linkedin.com/search/"
        category_map = {
            "posts": "content",
            "people": "people",
            "jobs": "jobs",
            "companies": "companies"
        }
        selected = self.category.lower() if hasattr(self, 'category') else 'posts'
        search_type = category_map.get(selected, "content")
        return f"{base}{search_type}/?keywords={self.search_query}"

    # =====================================================================================
 
    def clean_export_data(scraped_data: list[dict]):
        """Removes unwanted keys before export."""
        for post in scraped_data:
            if 'category' in post:  
                del post['category']
        return scraped_data