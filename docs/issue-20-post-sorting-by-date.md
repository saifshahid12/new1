# Issue 20: Allow Sorting Content by Date

## 📝 Overview
Task 20 introduces the ability to sort extracted LinkedIn posts based on their post date.
Previously, posts were exported in the order they were scraped. With this enhancement, users
can control the chronological order of exported data.

Supported sorting options:
- latest – Newest posts first
- oldest – Oldest posts first
- none – Original scraping order (default)

---

## 🎯 Objective
- Use the existing `Timestamp` field extracted from LinkedIn posts
- Allow users to define sorting preference via `config.json`
- Sort posts before exporting to CSV and JSON
- Preserve original order when sorting is disabled

---

## ⚙️ Implementation Details

### 1. Configuration Update
A new optional key is added inside `scraper_settings`:

```json
"scraper_settings": {
  "base_url": "https://www.linkedin.com/login",
  "search_query": "Python developer",
  "category": "Posts",
  "sort_by_date": "latest",
  "scroll_limit": 5,
  "max_scroll_attempts": 50
}


---

## 🧪 Testing

- **Unit Tests:** `tests/test_date_sorting.py` verifies:
  1. Correct date extraction from various formats
  2. Proper sorting with latest and oldest options
  3. none option preserves original order
  4. Mixed date scenarios handled correctly

- **Manual Testing:**
  1. Change sort_by_date in config.json to latest, oldest, none
  2. Run scraper
  3. Verify CSV/JSON shows posts in correct chronological order

---

## ✅ Benefits

 - Enables chronological analysis of content
 - Helps identify trending topics over time
 - Improves data organization for reporting
 - Works seamlessly with existing category and keyword filtering

---

## 🔗 References
 - LinkedIn Scraper Tool – Official Repo
 - LinkedInScraper class implementation (src/scraper.py)
 - export_data() function in src/utils.py
 - main.py – Sorting integration point