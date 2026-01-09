import logging
from src.utils import load_config, export_data, filter_posts_by_keyword
from src.scraper import LinkedInScraper
from selenium.common.exceptions import WebDriverException

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
        logging.info(f"Configuration loaded. Search query: '{search_query}'")
        logging.info(f"Scraping category selected: {category}")

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

        # Filter posts by keyword if search_query is provided
        processed_posts = filter_posts_by_keyword(scraped_data, search_query) if search_query else scraped_data

        # Ensure every post has correct Category and search_query
        for post in processed_posts:
            post["Category"] = category
            post["search_query"] = search_query
            # Remove any old lowercase 'category' key
            if "category" in post:
                del post["category"]

        # Export data (CSV + JSON)
        export_data(processed_posts, search_query, category,timestamp="timestamp")
        logging.info("Data export completed successfully")

        # Show summary
        matched = sum(1 for p in processed_posts if p.get("keyword_matched"))
        print(f"\n{'='*50}")
        print("SCRAPING COMPLETE")
        print(f"{'='*50}")
        print(f"Total posts scraped: {len(scraped_data)}")
        print(f"Posts matching '{search_query}': {matched}")
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
