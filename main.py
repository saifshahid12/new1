import logging
from src.utils import load_config, export_data, filter_posts_by_keyword, extract_emails_from_text
from src.scraper import LinkedInScraper
from selenium.common.exceptions import WebDriverException
from src.utils import mock_llm_validate_content


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("linkedin_scraper.log"),
        logging.StreamHandler()
    ]
)

def main():
    """Main function to initialize and run the LinkedIn scraper with category & search query support."""
    logging.info("--- LinkedIn Scraper Starting ---")
    
    scraper = None
    try:
        # Load configuration
        config = load_config()
        scraper_settings = config.get("scraper_settings", {})

        # Read search query and category from config
        search_query = scraper_settings.get("search_query", "")
        category = scraper_settings.get("category", "Posts")  # Default: Posts
        sort_order = scraper_settings.get("sort_by_date", "latest") 

        logging.info(f"Configuration loaded. Search query: '{search_query}'")
        logging.info(f"Scraping category selected: {category}")
        logging.info(f"Sort order: {sort_order}")

        # Initialize scraper
        scraper = LinkedInScraper(config)
        logging.info("Scraper initialized successfully")

        # Login
        scraper.login()
        logging.info("Login completed")

        # Perform search
        scraper.perform_search()
        logging.info("Search completed")

      


        # Human-like scrolling
        scraper.human_like_scroll()
        logging.info("Scrolling completed")

        # Extract posts
        scraper.extract_post_elements()
        scraped_data = scraper.scraped_data

        if not scraped_data:
            logging.warning("No posts were scraped. Check if you're on the correct page.")
            return

        logging.info(f"Extracted {len(scraped_data)} posts")

        # =================================================================
        # EMAIL EXTRACTION ADDED HERE (BEFORE SORTING) - DRY FIXED
        # =================================================================
        # Use single shared utility function from utils.py to avoid duplicate regex
        for post in scraped_data:
            text = post.get("Post Text", "")
            if text and text != "[No Text Content Found]":
                emails = extract_emails_from_text(text)  # Single source of truth
                if emails:
                    post["email"] = ", ".join(emails)
                    post["email_count"] = len(emails)
                    post["emails"] = emails
                else:
                    post["email"] = "No email found"
                    post["email_count"] = 0
                    post["emails"] = []
            else:
                post["email"] = "No text content"
                post["email_count"] = 0
                post["emails"] = []
        # =================================================================
        # END OF EMAIL EXTRACTION
        # =================================================================

        # NEW: Sort posts by date
        sorted_posts = scraper.sort_posts_by_date(scraped_data, sort_order)
        logging.info(f"Posts sorted by date ({sort_order} first)")

        # Filter posts by keyword if search_query is provided
        processed_posts = filter_posts_by_keyword(sorted_posts, search_query) if search_query else sorted_posts

        # Process each post
        for post in processed_posts:
            # Ensure every post has correct Category and search_query
            post["Category"] = category
            post["search_query"] = search_query

            # Remove any old lowercase 'category' key
            if "category" in post:
                del post["category"]

            # Remove Date_For_Sorting key before export (internal use only)
            if "Date_For_Sorting" in post:
                del post["Date_For_Sorting"] 

            # LLM validation - SAFE VERSION
            llm_result = mock_llm_validate_content(post.get("Post Text", ""))
            
            # Get values safely using .get() method
            email_present = llm_result.get("email_present", False)
            emails_list = llm_result.get("emails", [])
            
            # Add email field (already added above, but keep for consistency)
            if "email" not in post:  # If email not already added by regex extraction
                if email_present and emails_list:
                    post["email"] = emails_list[0]  # First email
                else:
                    post["email"] = "No email"
            
            # Add LLM validation results
            post["llm_validation"] = {
                "email_present": email_present,
                "emails": emails_list
            }

        # Export data (CSV + JSON)
        export_data(processed_posts, search_query, category, sort_order=sort_order)
        logging.info("Data export completed successfully")

        # Show summary
        matched = sum(1 for p in processed_posts if p.get("keyword_matched"))
        posts_with_emails = sum(1 for p in processed_posts if p.get("email_count", 0) > 0)
        
        print(f"\n{'='*50}")
        print("SCRAPING COMPLETE")
        print(f"{'='*50}")
        print(f"Total posts scraped: {len(scraped_data)}")
        print(f"Posts matching '{search_query}': {matched}")
        print(f"Posts with emails found: {posts_with_emails}")
        logging.info(f"Selected scraping category: {category}")
        print("Data saved to 'output/' folder")
        print("\nPress Enter to close browser and exit...")
        input()

    except FileNotFoundError as e:
        logging.critical(f"Configuration file missing: {e}")
    except ValueError as e:
        logging.critical(f"Configuration error: {e}")
    except WebDriverException as e:
        logging.critical(f"WebDriver error: {e}")
    except KeyboardInterrupt:
        logging.info("Scraping interrupted by user")
    except Exception as e:
        logging.error(f"Unexpected error: {e}", exc_info=True)
    finally:
        if scraper:
            scraper.close()
        logging.info("--- LinkedIn Scraper Finished ---")

if __name__ == "__main__":
    main()