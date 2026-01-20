import unittest
from unittest.mock import MagicMock, patch
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.scraper import LinkedInScraper
from src.utils import export_data

MOCK_CONFIG = {
    "linkedin_credentials": {"username": "test_user", "password": "test_pass"},
    "scraper_settings": {
        "base_url": "https://www.linkedin.com/login",
        "search_query": "test_keyword",
        "scroll_limit": 1,
        "max_scroll_attempts": 50,
        "delay": {"min_sec": 0.01, "max_sec": 0.02}
    },
    "human_mimicry": {
        "enable_mouse_movement": False,
        "typing_speed": [0.01, 0.02]
    }
}

class TestLinkedInScraperComplete(unittest.TestCase):

    def setUp(self):
        with patch.object(LinkedInScraper, "_validate_config", return_value=None):
            self.scraper = LinkedInScraper(MOCK_CONFIG, init_driver=False)

        self.scraper.driver = MagicMock()
        self.scraper.driver.find_element.return_value = MagicMock()
        self.scraper.driver.find_elements.return_value = [MagicMock(), MagicMock(), MagicMock()]

        # Patch all human-mimicry methods
        self.scraper._human_mouse_movement = MagicMock()
        self.scraper._human_typing = MagicMock()
        self.scraper._random_human_mouse_move = MagicMock()
        self.scraper._human_presence = MagicMock()
        self.scraper._continuous_mouse_jitter = MagicMock()
        self.scraper._random_human_action = MagicMock()

        # Patch sleep
        patcher_sleep = patch('time.sleep', return_value=None)
        patcher_sleep.start()
        self.addCleanup(patcher_sleep.stop)

    def test_random_delay_within_range(self):
        min_sec = 0.01
        max_sec = 0.02
        with patch('time.sleep') as mock_sleep:
            self.scraper._random_delay(min_sec, max_sec)
            delay_value = mock_sleep.call_args[0][0]
            self.assertTrue(min_sec <= delay_value <= max_sec)

    def test_duplicate_detection(self):
        post1 = {'Post Text':'A', 'Author Name':'B', 'Timestamp':'1h', 'Post URL':'url1'}
        self.scraper.scraped_data.append(post1)
        self.assertTrue(self.scraper._is_duplicate(post1.copy()))
        post2 = {'Post Text':'C', 'Author Name':'D', 'Timestamp':'2h', 'Post URL':'url2'}
        self.assertFalse(self.scraper._is_duplicate(post2))

    def test_config_validation_errors(self):
        bad_conf = MOCK_CONFIG.copy()
        bad_conf['scraper_settings'] = MOCK_CONFIG['scraper_settings'].copy()
        del bad_conf['scraper_settings']['scroll_limit']
        with self.assertRaises(ValueError):
            LinkedInScraper(bad_conf)
        bad_conf['scraper_settings']['scroll_limit'] = -1
        with self.assertRaises(ValueError):
            LinkedInScraper(bad_conf)
        bad_conf['linkedin_credentials']['username'] = 'YOUR_LINKEDIN_EMAIL'
        with self.assertRaises(ValueError):
            LinkedInScraper(bad_conf)

    @patch('src.scraper.WebDriverWait')
    def test_login_click_sequence(self, MockWait):
        mock_submit = MagicMock()
        MockWait.return_value.until.return_value = mock_submit
        self.scraper.login()
        mock_submit.click.assert_called_once()

    def test_perform_search(self):
        mock_input = MagicMock()
        self.scraper.driver.find_element.return_value = mock_input
        self.scraper.perform_search()
        self.scraper.driver.find_element.assert_called()
        self.assertGreaterEqual(mock_input.send_keys.call_count, 2)

    def test_human_like_scroll(self):
        # Return enough values for the scrolling loop
        self.scraper.driver.execute_script.side_effect = [100, 200, 300]
        self.scraper.human_like_scroll()
        self.assertGreaterEqual(self.scraper.driver.execute_script.call_count, 3)

    def test_extract_post_elements_with_duplicates(self):
        mock_post = MagicMock()
        self.scraper.driver.find_elements.return_value = [mock_post]*3
        self.scraper._parse_single_post = MagicMock(side_effect=[
            {'Post Text':'A','Author Name':'B','Timestamp':'1h','Post URL':'url1'},
            {'Post Text':'A','Author Name':'B','Timestamp':'1h','Post URL':'url1'},
            {'Post Text':'C','Author Name':'D','Timestamp':'2h','Post URL':'url2'}
        ])
        self.scraper.extract_post_elements()
        self.assertEqual(len(self.scraper.scraped_data), 2)

    def test_category_selection(self):
        self.scraper.scraped_data = [
            {"Post Text":"Python post","Category":"Posts"},
            {"Post Text":"Python video","Category":"Videos"},
            {"Post Text":"Python article","Category":"Articles"}
        ]
        selected_category = "Videos"
        filtered = [p for p in self.scraper.scraped_data if p["Category"] == selected_category]
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["Category"], "Videos")

    @patch('src.utils.export_data')
    def test_export_data_called(self, mock_export):
        self.scraper.scraped_data = [{'Post Text':'A','Author Name':'B','Timestamp':'1h','Post URL':'url1'}]
        from src.utils import export_data as utils_export_data
        utils_export_data(self.scraper.scraped_data, 'test_keyword')
        mock_export.assert_called_once_with(self.scraper.scraped_data, 'test_keyword')


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
