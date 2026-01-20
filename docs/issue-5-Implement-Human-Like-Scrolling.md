# Documentation for Issue 05: Implement Human-Like Scrolling

**Category:** Backend  
**Priority:** MUST-HAVE  
**Status:** Completed  

---

## 1. Objective

To scroll through the LinkedIn search results page in a human-like manner.  
This behavior triggers LinkedIn’s infinite scrolling mechanism, ensuring that all posts progressively load into the DOM for extraction.

---

## 2. Implementation Checklist

| Item                  | Status | Notes |
|----------------------|--------|-------|
| Slow scroll function | [x]    | Implemented using small, incremental scroll steps. |
| Random delays        | [x]    | `_random_delay()` introduces variable pauses between scroll actions. |
| Infinite scroll handling | [x] | Stops when scroll height no longer increases or when `scroll_limit` is reached. |

---

## 3. Key Code  
### **File:** `src/scraper.py`  
### **Method:** `human_like_scroll`

The scrolling logic uses JavaScript (`window.scrollTo`) and randomized increments to mimic real user behavior.

```python
import random
# ... (in LinkedInScraper class)

def _random_delay(self, min_time=1.0, max_time=3.0):
    """Pauses execution for a random period."""
    time.sleep(random.uniform(min_time, max_time))

def human_like_scroll(self):
    scroll_limit = self.config['scraper_settings'].get('scroll_limit', 10)
    scroll_count = 0 
    last_height = self.driver.execute_script("return document.body.scrollHeight")
    
    while scroll_count < scroll_limit:
        # Loop for small, incremental scrolls
        scroll_position = 0
        target_scroll_height = self.driver.execute_script("return document.body.scrollHeight")
        
        while scroll_position < target_scroll_height:
            scroll_position += random.uniform(200, 400)  # Variable scroll step size
            self.driver.execute_script(f"window.scrollTo(0, {scroll_position});")
            self._random_delay(0.5, 1.0)  # Short delay between steps

        self._random_delay(2.0, 4.0)  # Longer delay after section load
        
        # Check for new content
        new_height = self.driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break 
        
        last_height = new_height
        scroll_count += 1
```

---

## 4. Summary

The `human_like_scroll()` method ensures:

- Smooth, natural scrolling  
- Random imprecision like a human user  
- Consistent triggering of LinkedIn’s infinite scrolling  
- All dynamically loaded content becomes available for scraping  

This prepares the DOM with all required posts before the extraction phase begins.

---

If you'd like, I can also generate **Task 05 documentation in .md format**.
