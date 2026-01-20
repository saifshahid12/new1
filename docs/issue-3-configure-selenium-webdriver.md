# Documentation – Issue 03: Configure Selenium WebDriver (ChromeDriver)

**Category:** Backend  
**Priority:** MUST-HAVE  
**Status:** Completed  

---

## 1. Objective

To configure the Selenium WebDriver to automatically manage and launch the Chrome browser, ensuring a stable connection between the Python script and the browser window.

---

## 2. Implementation Checklist

| Item                           | Status | Notes                                                             |
|-------------------------------|--------|-------------------------------------------------------------------|
| Download correct driver version | [x]    | Handled automatically by `webdriver-manager`.                     |
| Connect driver with Selenium  | [x]    | Using `ChromeService(ChromeDriverManager().install())`.           |
| Test browser launch           | [x]    | Tested within the `main.py` execution flow.                       |

---

## 3. Key Code (`src/scraper.py` - `_setup_driver`)

The `webdriver-manager` library automatically installs the correct ChromeDriver, removing the need for manual downloads.

```python
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver

# ...

def _setup_driver(self):
    """Sets up the Chrome WebDriver using WebDriver Manager."""
    
    # ... options configuration ...
    options = webdriver.ChromeOptions()
    # Add any required options here (headless, disable warnings, etc.)
    
    # Initialize the Chrome driver using the service manager
    service = ChromeService(ChromeDriverManager().install())
    self.driver = webdriver.Chrome(service=service, options=options)
    self.driver.maximize_window()
```

The browser launches with predefined options and automatically maximizes the window for better visibility and compatibility.

---
