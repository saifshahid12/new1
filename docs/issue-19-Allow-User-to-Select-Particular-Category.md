# Issue 19: Allow User to Select a Particular Category

## 📝 Overview
Task 19 focuses on giving the user the ability to **select a specific category** of content to scrape from LinkedIn.  
Previously, the scraper would extract all posts, but now users can choose a category such as:

- `Posts`
- `People`
- `Jobs`
- `Companies`
- `Videos`

This makes the scraper more flexible and targeted.

---

## 🎯 Objective
- Let the user specify the desired category in the configuration (`config.json`) or via input.
- Filter scraping to only extract content from the selected category.
- Ensure that exported data (CSV/JSON) corresponds only to the selected category.

---

## ⚙️ Implementation Details

1. **Configuration Update**
   - Added `scraper_settings["category"]` in `config.json`.
   - Example:
     ```json
     "scraper_settings": {
         "base_url": "https://www.linkedin.com/login",
         "search_query": "Python developer",
         "category": "Posts",
         "scroll_limit": 5,
         "max_scroll_attempts": 50,
         "delay": {"min_sec": 1.5, "max_sec": 4.0}
     }
     ```

2. **Scraper Modification**
   - The `LinkedInScraper` class now reads the category from config.
   - During scraping, only elements belonging to the selected category are extracted.
   - Logging messages reflect the selected category:
     ```
     Scraping Category Selected: Posts
     ```

3. **Data Export**
   - Exported CSV and JSON include only posts of the selected category.
   - File naming convention reflects the category:
     ```
     Python_developer_Posts_posts_YYYYMMDD_HHMMSS.csv
     ```

---

## 🧪 Testing

- **Unit Tests:** `tests/test_category.py` verifies:
  1. Correct category is read from config.
  2. Scraper extracts only elements of the selected category.
  3. Exported data matches the selected category.
  
- **Manual Testing:**
  1. Change `category` in `config.json`.
  2. Run scraper.
  3. Verify that CSV/JSON contains only the specified category.

---

## ✅ Benefits

- Reduces unnecessary scraping.
- Saves time and resources.
- Makes analysis more focused and organized.
- Fully compatible with existing filtering by keywords.

---

## 🔗 References
- LinkedIn Scraper Tool – Official Repo
- `LinkedInScraper` class implementation
- `export_data()` function in `src/utils.py`
