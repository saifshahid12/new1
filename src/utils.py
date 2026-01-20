import csv
import json
import os
from datetime import datetime
import logging
from dotenv import load_dotenv
import re 

load_dotenv()

def load_config(config_path="config/config.json"):

    """Load configuration from JSON file."""

    # path of config 
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"{config_path} not found")

    # read config file 
    with open(config_path, "r", encoding="utf-8") as f:

        return json.load(f)

    # ====================================================================================

def load_credentials():

    # load email and password from .env
    """Load LinkedIn credentials from .env file."""
    username = os.getenv("LINKEDIN_USERNAME")
    password = os.getenv("LINKEDIN_PASSWORD")

    # condition for email pasword if not in .env
    if not username or not password:
        raise ValueError("LinkedIn credentials missing in .env")

    return username, password

    # =====================================================================================

def filter_posts_by_keyword(posts, keyword):

    """Mark posts that contain the keyword (case-insensitive)."""

    for post in posts:

        # use get method for geting text of posts 
        text = post.get("Post Text", "").lower()

        post["keyword_matched"] = keyword.lower() in text if keyword else False

    return posts

    # ====================================================================================

def export_data(data, search_query, category,timestamp=None, sort_order="none"):


    """
    Exports scraped posts to CSV and JSON with fixed Category and search_query.

    Args:

        data (list): List of post dictionaries
        search_query (str): Search query used
        category (str): Category selected  
        timestamp (str, optional): Timestamp for filename
        sort_order (str): Sorting order used ("latest", "oldest", "none")
    
    """

    if timestamp is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")


    # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_query = search_query.replace(" ", "_") if search_query else "LinkedIn"

    # Ensure every post has search_query and Category
    for post in data:
        post["search_query"] = search_query
        post["Category"] = category


        if "category" in post:  
            del post["category"]

        # Extract emails from post text
        post_text = post.get("Post Text", "")

        if post_text and post_text != "[No Text Content Found]":
            emails = extract_emails_from_text(post_text)

            if emails:
                post["email"] = ", ".join(emails)  # Join multiple emails
                post["email_count"] = len(emails)
                post["emails"] = emails  # List of emails

            else:
                post["email"] = "No email found"
                post["email_count"] = 0
                post["emails"] = []
        else:
            post["email"] = "No text content"
            post["email_count"] = 0
            post["emails"] = []
        
        # Ensure llm_validation exists with email info
        if "llm_validation" not in post:
            post["llm_validation"] = {
                "email_present": len(emails) > 0,
                "emails": emails
            }
        else:
            # Update llm_validation with actual emails found
            post["llm_validation"]["email_present"] = len(emails) > 0
            post["llm_validation"]["emails"] = emails
    output_dir = os.path.join(os.getcwd(), "output")
    os.makedirs(output_dir, exist_ok=True)

    csv_file = os.path.join(output_dir, f"{safe_query}_{category}_posts_{timestamp}.csv")
    json_file = os.path.join(output_dir, f"{safe_query}_{category}_posts_{timestamp}.json")

    # Export CSV
    fieldnames = ['Post Text', 'Author Name', 'Timestamp', 'Post URL', 'Category', 'keyword_matched', 'search_query', 'email','email_count', 'emails', 'llm_validation']
    try:
        # FIX: dynamic fieldnames
        fieldnames = set()
        for item in data:
            fieldnames.update(item.keys())

        fieldnames = list(fieldnames)
        with open(csv_file, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

        logging.info(f"Data exported to CSV: {csv_file}")
        
    except Exception as e:
        logging.error(f"Error exporting CSV: {e}")

    # Export JSON
    # Export JSON WITH METADATA
    try:
        json_output = {
            "metadata": {
                "export_timestamp": timestamp,
                "search_query": search_query,
                "category": category,
                "sort_order": sort_order,
                "total_posts": len(data),
                "matched_posts": sum(1 for p in data if p.get("keyword_matched", False))
            },
            "posts": data  # This is already sorted
        }
        
        with open(json_file, mode='w', encoding='utf-8') as f:
            json.dump(json_output, f, ensure_ascii=False, indent=4)

        logging.info(f"Data exported to JSON: {json_file}")
        
    except Exception as e:
        logging.error(f"Error exporting JSON: {e}")
    
    return csv_file, json_file

    # ===================================================================================

def mock_llm_validate_content(text: str) -> dict:
    
    """
    Mock LLM validation for scraped content.

    Purpose:
    - Simulates LLM behavior for Task 21
    - Detects presence of email addresses in given text
    - Returns structured response for unit testing

    Note:
    - Uses regex-based extraction
    - Designed to satisfy Task 21 test cases only
    """
    import re

    if not text:
        return {
            "email_present": False,
            "emails": []
        }

    email_pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
    emails = re.findall(email_pattern, text)

    result = {
        "email_present": len(emails) > 0,
        "emails": list(set(emails))
    }

    logging.debug(f"Mock LLM validation: found {len(emails)} emails")
    return result

    # ====================================================================================
    
# Email regex logic exists both here and in main.py.
# This is intentional to keep utils export independent of main execution flow.
# Refactoring into a shared helper was avoided to prevent scope changes.

def extract_emails_from_text(text: str) -> list:

    """Extract email addresses from text using regex."""
    import re
    if not text:
        return []
    
    # Improved email regex pattern
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    
    # Filter out common false positives
    filtered_emails = []
    for email in emails:
        # Skip if looks like a domain without proper email
        if email.count('@') != 1:
            continue
        # Skip if too short
        if len(email) < 5:
            continue
        # Skip if contains "example" or "test"
        if any(word in email.lower() for word in ["example", "test", "domain", "email"]):
            continue
        filtered_emails.append(email)
    
    return list(set(filtered_emails))  


    # ======================================================================================