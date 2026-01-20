# Task 9: Export Data to CSV & JSON

## Category

Backend (MUST-HAVE)

## Objective

Task 08 is responsible for **persisting filtered LinkedIn post data** into structured files for later analysis. The scraper exports data into **CSV** (primary) and **JSON** (backup) formats.

---

## Why This Task Is Important

Without Task 08, scraped data only exists in memory. Exporting enables:

* Data analysis
* Reporting
* Sharing results
* Long-term storage

---

## Input

* `data` → List of filtered post dictionaries (output of Task 07)
* `search_query` → String used to name output files

---

## Output Formats

### 1. CSV File (Primary)

* Human-readable
* Compatible with Excel, Google Sheets, Pandas

### 2. JSON File (Secondary)

* Structured
* Useful for APIs or re-processing

---

## File Naming Convention

```text
<search_query>_linkedin_posts_<timestamp>.csv
<search_query>_linkedin_posts_<timestamp>.json
```

Example:

```text
Python_web_scraping_linkedin_posts_20251216_101530.csv
```

---

## Storage Location

```text
/output/
```

(The folder is auto-created if missing)

---

## Processing Logic

1. Sanitize search query for filenames
2. Generate timestamp
3. Detect CSV headers dynamically from dictionary keys
4. Write CSV using `csv.DictWriter`
5. Write JSON using `json.dump`

---

## Implementation Location

* **Function**: `export_data`
* **File**: `src/utils.py`
* **Called from**: `main.py`

---

## Error Handling

* Skips export if data is empty
* Handles file I/O exceptions safely
* UTF-8 encoding for text safety

---

## Completion Criteria

* CSV and JSON files created successfully
* Correct headers
* No data loss
* Compatible with Excel & Pandas

---

## Status

✅ Implemented and tested
