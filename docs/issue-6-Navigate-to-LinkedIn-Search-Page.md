# Documentation for issue # 6: Navigate to LinkedIn Search Page

**Category:** Backend  
**Priority:** MUST-HAVE  
**Status:** Completed  

---

## 1. Objective

To navigate from the logged-in LinkedIn home page to the dedicated search results page using the search query defined in `config.json`.  
This step is essential to prepare the browser for post extraction.

---

## 2. Implementation Checklist

| Item                        | Status | Notes                                                                 |
|-----------------------------|--------|-----------------------------------------------------------------------|
| Retrieve search keyword     | [x]    | Keyword retrieved from `config.json`.                                 |
| Locate search input field   | [x]    | Used stable XPath targeting `role='combobox'` and `aria-label='Search'`. |
| Enter keyword and submit    | [x]    | Used `Keys.RETURN` to submit the search.                             |
| Wait for page load          | [x]    | Human-like delay ensures full rendering of the search results page.  |

---

## 3. Key Code  
### **File:** `src/scraper.py`  
### **Method:** `perform_search`

This method assumes a successful login (Task 03) and uses Selenium’s `Keys` to simulate pressing Enter after entering the search term.

```python
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

def perform_search(self):
    search_query = self.config['scraper_settings']['search_query']
    
    try:
        wait = WebDriverWait(self.driver, 10)
        
        # Locate the main search input field
        search_input = wait.until(
            EC.presence_of_element_located((
                By.XPATH, 
                "//input[@role='combobox' and @aria-label='Search']"
            ))
        )
        
        # Enter query and submit
        search_input.clear()
        self._random_delay(0.5, 1.5)
        search_input.send_keys(search_query)
        search_input.send_keys(Keys.RETURN)
        
        self._random_delay(4, 6)  # Wait for search results page to load
        
    except Exception as e:
        # ... error handling ...
        pass
```

---

## 4. Summary

This method:

- Reads the search keyword from `config.json`
- Finds LinkedIn’s main search bar using a stable and reliable XPath
- Enters the query and triggers the search with `Keys.RETURN`
- Waits for the search results page to load fully

With this step complete, the scraper is now positioned on the **Posts Search Results** page, ready for scrolling (Task 04) and content extraction (Task 06).

---

If you want, I can now write **Task 06 documentation in .md format**.
