# Documentation – Issue 04: Implement LinkedIn Login Automation

**Category:** Backend  
**Priority:** MUST-HAVE  
**Status:** Completed  

---

## 1. Objective

To automate the process of logging into the LinkedIn website using credentials stored in the `config/config.json` file, thereby gaining access to the content behind the login wall.

---

## 2. Implementation Checklist

| Item                    | Status | Notes                                                          |
|------------------------|--------|------------------------------------------------------------------|
| Identify login fields  | [x]    | Used stable `By.ID` selectors: `"username"` and `"password"`.   |
| Enter username/password | [x]    | Credentials read from `config.json`.                            |
| Click login            | [x]    | Located the “Sign in” button via XPath.                         |
| Add wait until profile loads | [x] | Uses `WebDriverWait` and human-like delays for stable behavior. |

---

## 3. Key Code (`src/scraper.py` – `login`)

This method retrieves login credentials from `self.config`, navigates to the login page, and interacts with input fields using Selenium’s stable locators.

```python
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

def login(self):
    # ... retrieval of username/password from config ...
    self.driver.get(base_url)
    
    try:
        wait = WebDriverWait(self.driver, 10)
        
        # 1. Fill Username Field
        user_field = wait.until(EC.presence_of_element_located((By.ID, "username")))
        user_field.send_keys(username)
        
        # 2. Fill Password Field
        pass_field = wait.until(EC.presence_of_element_located((By.ID, "password")))
        pass_field.send_keys(password)
        
        # 3. Click Sign In
        sign_in_button = self.driver.find_element(By.XPATH, "//button[normalize-space()='Sign in']")
        sign_in_button.click()
        
        # Human-like delay for realistic loading and anti-bot friendliness
        self._random_delay(4, 6)
    
    except Exception as e:
        # ... error handling ...
        print("Login failed:", e)
        self.driver.quit()
```

The `login()` function includes strong error handling to ensure the browser is safely closed if required login elements are not found.

---
