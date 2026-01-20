import unittest
from unittest.mock import patch, MagicMock
from src.scraper import LinkedInScraper
from src.utils import filter_posts_by_keyword, export_data


class TestErrorHandling(unittest.TestCase):
    """Tests for Task 11: Error Handling & Stability"""

    def setUp(self):
        self.config = {
            "linkedin_credentials": {
                "username": "test",
                "password": "test"
            },
            "scraper_settings": {
                "base_url": "https://www.linkedin.com/login",
                "search_query": "python",
                "scroll_limit": 1,
                "max_scroll_attempts": 1
            }
        }

    # -------------------------------
    # Task 11: Filter Error Safety
    # -------------------------------
    def test_filter_posts_with_invalid_data(self):
        """Filtering should not crash with malformed post data"""
        posts = [
            {"Post Text": "This is a Python scraping post"},
            {"Post Text": "User A"}
        ]

        result = filter_posts_by_keyword(posts, "python")

        # ALL posts must be returned
        self.assertEqual(len(result), 2)

        # First post matches keyword
        self.assertTrue(result[0]["keyword_matched"])

        # Second post does NOT match keyword but still included
        self.assertFalse(result[1]["keyword_matched"])

    # -------------------------------
    # Task 11: Export Error Handling
    # -------------------------------
    @patch("builtins.open", side_effect=Exception("Disk error"))
    def test_export_data_logs_error(self, mock_open):
        """Export should log error instead of crashing"""
        with self.assertLogs(level="ERROR") as log:
            export_data([{"Post Text": "test"}], "query", "Posts")

        self.assertTrue(
            any("error" in message.lower() for message in log.output)
        )

    # -------------------------------
    # Task 11: Safe Browser Shutdown
    # -------------------------------
    def test_browser_close_safe(self):
        """Closing browser should never crash"""
        scraper = LinkedInScraper(self.config)

        mock_driver = MagicMock()
        scraper.driver = mock_driver

        scraper.close()

        mock_driver.quit.assert_called_once()

    # -------------------------------
    # Task 11: Scroll Error Safety
    # -------------------------------
    def test_scroll_error_handled_gracefully(self):
        """Scroll failure should not crash scraper"""
        scraper = LinkedInScraper(self.config)
        scraper.driver = MagicMock()
        scraper.driver.execute_script.side_effect = Exception("Scroll failed")

        with self.assertLogs(level="ERROR"):
            scraper.human_like_scroll()


if __name__ == "__main__":
    unittest.main()
