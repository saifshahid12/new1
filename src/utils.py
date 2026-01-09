import csv
import json
import os
from datetime import datetime
import logging
from dotenv import load_dotenv

load_dotenv()

def load_config(config_path="config/config.json"):
    """Load configuration from JSON file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"{config_path} not found")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_credentials():
    """Load LinkedIn credentials from .env file."""
    username = os.getenv("LINKEDIN_USERNAME")
    password = os.getenv("LINKEDIN_PASSWORD")
    if not username or not password:
        raise ValueError("LinkedIn credentials missing in .env")
    return username, password

def filter_posts_by_keyword(posts, keyword):
    """Mark posts that contain the keyword (case-insensitive)."""
    for post in posts:
        text = post.get("Post Text", "").lower()
        post["keyword_matched"] = keyword.lower() in text if keyword else False
    return posts

def export_data(data, search_query, category,timestamp):
    """Exports scraped posts to CSV and JSON with fixed Category and search_query."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_query = search_query.replace(" ", "_") if search_query else "LinkedIn"

    # Ensure every post has search_query and Category
    for post in data:
        post["search_query"] = search_query
        post["Category"] = category
        if "category" in post:  
            del post["category"]

    output_dir = os.path.join(os.getcwd(), "output")
    os.makedirs(output_dir, exist_ok=True)

    csv_file = os.path.join(output_dir, f"{safe_query}_{category}_posts_{timestamp}.csv")
    json_file = os.path.join(output_dir, f"{safe_query}_{category}_posts_{timestamp}.json")

    # Export CSV
    fieldnames = ['Post Text', 'Author Name', 'Timestamp', 'Post URL', 'Category', 'keyword_matched', 'search_query']
    try:
        with open(csv_file, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        logging.info(f"Data exported to CSV: {csv_file}")
    except Exception as e:
        logging.error(f"Error exporting CSV: {e}")

    # Export JSON
    try:
        with open(json_file, mode='w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logging.info(f"Data exported to JSON: {json_file}")
    except Exception as e:
        logging.error(f"Error exporting JSON: {e}")

    return csv_file, json_file
