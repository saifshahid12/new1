# Documentation – Issue 02: Set Up Python Development Environment

**Category:** Backend  
**Priority:** MUST-HAVE  
**Status:** Completed  

---

## 1. Objective

To prepare the local machine and Python environment by installing necessary tools and libraries to support the scraper's operation.

---

## 2. Implementation Checklist

| Item                           | Status | Notes                                                      |
|-------------------------------|--------|------------------------------------------------------------|
| Install Python & Virtual Environment | [x]    | Python 3.x installed and a virtual environment created.    |
| Install Selenium, pandas      | [x]    | Core scraping and data handling libraries installed.       |
| Set up project folders        | [x]    | Created `main.py`, `src/`, `src/scraper.py`, `src/utils.py`, and `config/config.json`. |

---

## 3. Setup Steps

### **Virtual Environment Setup**

```bash
python -m venv venv
source venv/bin/activate      # On Linux/macOS
venv\Scripts\activate         # On Windows
```

---

### **Install Dependencies**

Install required libraries:

```bash
pip install selenium pandas webdriver-manager
```

**selenium** – For browser automation.  
**pandas** – For structured data manipulation and CSV/JSON export.  
**webdriver-manager** – Automatically manages the correct ChromeDriver version.

---
