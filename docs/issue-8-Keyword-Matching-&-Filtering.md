# Task 8: Keyword Matching & Filtering

## Category

Backend (MUST-HAVE)

## Objective

The purpose of Task 07 is to **filter scraped LinkedIn posts** based on user-provided keywords. This ensures that only **relevant posts** are retained for storage and analysis, reducing noise and improving data quality.

---

## Why This Task Is Important

After Task 06, the scraper collects **all visible posts**, including irrelevant ones. Task 07 acts as a **logical filter layer** that:

* Narrows down results
* Improves performance for export
* Aligns output with user intent

---

## Input

* `posts` → List of dictionaries generated from Task 06
* `keyword` → A string keyword provided by the user (via config or runtime)

Example post structure:

```python
{
    "Post Text": "Learning Python web scraping with Selenium",
    "Author Name": "John Doe",
    "Timestamp": "2h",
    "Post URL": "https://linkedin.com/posts/..."
}
```

---

## Processing Logic

1. Convert the keyword to lowercase
2. Loop through each post
3. Extract the post text field
4. Perform a **case-insensitive substring match**
5. Store only matched posts

---

## Implementation Location

* **Function**: `filter_posts_by_keyword`
* **File**: `src/utils.py`
* **Called from**: `main.py`

---

## Output

* A new list containing **only matched posts**

Example output:

```python
filtered_posts = [post1, post3, post7]
```

---

## Edge Cases Handled

* Empty keyword → returns empty list
* Empty posts list → returns empty list
* Posts without text → safely ignored

---

## Completion Criteria

* Function correctly filters posts
* Case-insensitive matching
* No crash on missing fields
* Successfully integrated into main execution flow

---

## Status




✅ Implemented and tested
