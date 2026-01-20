# Documentation for Task 07: Extract Post Elements (HTML Parsing)

**Category:** Backend  
**Priority:** MUST-HAVE  
**Status:** Completed  

---

## 1. Objective

To locate all post container elements loaded on the LinkedIn search results page after scrolling, and extract the four required data fields from each post:

- Post Text  
- Author Name  
- Timestamp  
- Post URL  

---

## 2. Implementation Checklist

| Item                     | Status | Notes                                                                 |
|--------------------------|--------|-----------------------------------------------------------------------|
| Locate post containers   | [x]    | Used XPath matching `feed-shared-update-v2` post components.          |
| Handle “see more” button | [x]    | Clicks expand button to reveal full post text when present.           |
| Extract all fields       | [x]    | Author, timestamp, text, and URL extracted using relative XPaths.    |
| Store structured data    | [x]    | Data appended as dictionaries to `self.scraped_data`.                |

---

## 3. Key Code  
### **File:** `src/scraper.py`  
### Methods: `extract_post_elements` + `_parse_single_post`

The extraction system first identifies top-level post containers, then parses each post using individual field-level XPaths.

```python
from selenium.common.exceptions import NoSuchElementException

# --- Extraction Function ---
def extract_post_elements(self):
    POST_CONTAINER_XPATH = "//div[contains(@class, 'feed-shared-update-v2') or contains(@class, 'update-components-update-v2')]"
    
    # ... wait for elements and loop through containers ...
    for post_element in post_containers:
        post_data = self._parse_single_post(post_element)
        if post_data and not self._is_duplicate(post_data):
            self.scraped_data.append(post_data)

# --- Parsing Helper Function ---
def _parse_single_post(self, post_element):
    data = {}
    
    # 1. Handle 'see more' button and extract Post Text
    try:
        see_more_button = post_element.find_element(By.XPATH, ".//button[text()='...see more']")
        self.driver.execute_script("arguments[0].click();", see_more_button)
        self._random_delay(0.2, 0.5)
    except NoSuchElementException:
        pass 

    text_element = post_element.find_element(By.XPATH, ".//div[contains(@class, 'update-components-text')]")
    data['Post Text'] = text_element.text.strip().replace('\n', ' ')

    # 2. Extract Author Name
    author_element = post_element.find_element(By.XPATH, ".//span[@class='update-components-actor__name']//span[@aria-hidden='true']")
    data['Author Name'] = author_element.text.strip()
    
    # 3. Extract Timestamp
    timestamp_element = post_element.find_element(By.XPATH, ".//span[contains(@class, 'update-components-header__timestamp')]")
    data['Timestamp'] = timestamp_element.get_attribute('aria-label').strip()
    
    # 4. Extract Post URL
    post_link_element = post_element.find_element(By.XPATH, ".//a[contains(@href, '/update/urn:li:activity:')]")
    data['Post URL'] = post_link_element.get_attribute('href')
    
    return data
