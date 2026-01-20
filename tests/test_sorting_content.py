"""
test_date_sorting.py
Unit tests for Task 20: Sorting Content by Date
"""
import unittest
from datetime import datetime, timedelta
from src.scraper import LinkedInScraper

class TestDateSorting(unittest.TestCase):
    """Test cases for date extraction and sorting functionality."""
    
    def setUp(self):
        """Set up test configuration."""
        self.config = {
            "scraper_settings": {
                "base_url": "https://www.linkedin.com/login",
                "search_query": "test",
                "scroll_limit": 5,
                "sort_by_date": "latest"
            }
        }
        self.scraper = LinkedInScraper(self.config, init_driver=False)
    
    def test_extract_date_from_iso_format(self):
        """Test extracting date from ISO timestamp format."""
        test_cases = [
            ("2024-03-15T10:30:00.000Z", datetime(2024, 3, 15)),
            ("2023-12-01T08:15:00.000Z", datetime(2023, 12, 1)),
            ("2024-01-31T23:59:59.999Z", datetime(2024, 1, 31)),
        ]
        
        for timestamp, expected_date in test_cases:
            result = self.scraper._extract_date_for_sorting(timestamp)
            self.assertEqual(result.date(), expected_date.date())
    
    def test_extract_date_from_relative_time(self):
        """Test extracting date from relative time strings."""
        now = datetime.now()
        
        # Test "days ago"
        result = self.scraper._extract_date_for_sorting("2 days ago")
        expected = now - timedelta(days=2)
        self.assertAlmostEqual(result.date(), expected.date())
        
        # Test "weeks ago"
        result = self.scraper._extract_date_for_sorting("1 week ago")
        expected = now - timedelta(weeks=1)
        self.assertAlmostEqual(result.date(), expected.date())
    
    def test_sort_posts_latest_first(self):
        """Test sorting posts with latest first."""
        posts = [
            {'Post Text': 'Post 1', 'Date_For_Sorting': datetime(2024, 1, 15)},
            {'Post Text': 'Post 2', 'Date_For_Sorting': datetime(2024, 3, 10)},
            {'Post Text': 'Post 3', 'Date_For_Sorting': datetime(2024, 2, 20)},
        ]
        
        sorted_posts = self.scraper.sort_posts_by_date(posts, "latest")
        
        # Should be: Post 2 (Mar 10), Post 3 (Feb 20), Post 1 (Jan 15)
        self.assertEqual(sorted_posts[0]['Post Text'], 'Post 2')
        self.assertEqual(sorted_posts[1]['Post Text'], 'Post 3')
        self.assertEqual(sorted_posts[2]['Post Text'], 'Post 1')
    
    def test_sort_posts_oldest_first(self):
        """Test sorting posts with oldest first."""
        posts = [
            {'Post Text': 'Post 1', 'Date_For_Sorting': datetime(2024, 3, 10)},
            {'Post Text': 'Post 2', 'Date_For_Sorting': datetime(2024, 1, 15)},
            {'Post Text': 'Post 3', 'Date_For_Sorting': datetime(2024, 2, 20)},
        ]
        
        sorted_posts = self.scraper.sort_posts_by_date(posts, "oldest")
        
        # Should be: Post 2 (Jan 15), Post 3 (Feb 20), Post 1 (Mar 10)
        self.assertEqual(sorted_posts[0]['Post Text'], 'Post 2')
        self.assertEqual(sorted_posts[1]['Post Text'], 'Post 3')
        self.assertEqual(sorted_posts[2]['Post Text'], 'Post 1')
    
    def test_sort_posts_mixed_dates(self):
        """Test sorting posts with some having dates and some without."""
        posts = [
            {'Post Text': 'Post 1', 'Date_For_Sorting': datetime(2024, 3, 10)},
            {'Post Text': 'Post 2', 'Date_For_Sorting': None},
            {'Post Text': 'Post 3', 'Date_For_Sorting': datetime(2024, 1, 15)},
            {'Post Text': 'Post 4', 'Date_For_Sorting': None},
        ]
        
        sorted_posts = self.scraper.sort_posts_by_date(posts, "latest")
        
        # Posts with dates should come first, sorted latest to oldest
        # Then posts without dates in original order
        self.assertEqual(sorted_posts[0]['Post Text'], 'Post 1')  # Mar 10
        self.assertEqual(sorted_posts[1]['Post Text'], 'Post 3')  # Jan 15
        self.assertEqual(sorted_posts[2]['Post Text'], 'Post 2')  # No date
        self.assertEqual(sorted_posts[3]['Post Text'], 'Post 4')  # No date
    
    def test_sort_order_none(self):
        """Test that 'none' sort order returns original order."""
        posts = [
            {'Post Text': 'Post 1', 'Date_For_Sorting': datetime(2024, 3, 10)},
            {'Post Text': 'Post 2', 'Date_For_Sorting': datetime(2024, 1, 15)},
            {'Post Text': 'Post 3', 'Date_For_Sorting': datetime(2024, 2, 20)},
        ]
        
        sorted_posts = self.scraper.sort_posts_by_date(posts, "none")
        
        # Should remain in original order
        self.assertEqual(sorted_posts[0]['Post Text'], 'Post 1')
        self.assertEqual(sorted_posts[1]['Post Text'], 'Post 2')
        self.assertEqual(sorted_posts[2]['Post Text'], 'Post 3')

if __name__ == '__main__':
    unittest.main()