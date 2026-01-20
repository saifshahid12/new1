import unittest
from unittest.mock import patch, MagicMock
from src.scraper import LinkedInScraper


class TestAntiBotHumanMimicry(unittest.TestCase):

    def setUp(self):
        self.mock_config = {
            "scraper_settings": {
                "base_url": "https://www.linkedin.com/login",
                "search_query": "Python",
                "scroll_limit": 1
            },
            "human_mimicry": {
                "enable_mouse": True,
                "enable_typing": True,
                "enable_random_actions": True,
                "typing_speed": [0.01, 0.02],
                "mouse_move_x_range": [-5, 5],
                "mouse_move_y_range": [-5, 5],
                "random_action_probability": 1.0
            }
        }

        self.scraper = LinkedInScraper(self.mock_config, init_driver=False)
        self.scraper.driver = MagicMock()

    # --------------------------------------------------
    # Mouse Movement (external boundary only)
    # --------------------------------------------------
    @patch("src.scraper.ActionChains")
    def test_random_human_mouse_move_executes(self, mock_chain):
        mock_chain.return_value = MagicMock()

        try:
            self.scraper._random_human_mouse_move()
        except Exception as e:
            self.fail(f"_random_human_mouse_move crashed: {e}")

    # --------------------------------------------------
    # Continuous Mouse Jitter
    # --------------------------------------------------
    @patch("src.scraper.ActionChains")
    def test_continuous_mouse_jitter_executes(self, mock_chain):
        mock_chain.return_value = MagicMock()

        try:
            self.scraper._continuous_mouse_jitter(duration=0.1)
        except Exception as e:
            self.fail(f"_continuous_mouse_jitter crashed: {e}")

    # --------------------------------------------------
    # Human Typing
    # --------------------------------------------------
    def test_human_typing_sends_each_character(self):
        element = MagicMock()

        self.scraper._human_typing(element, "test")

        self.assertEqual(element.send_keys.call_count, 4)

    # --------------------------------------------------
    # Edge Case: Empty String Typing
    # --------------------------------------------------
    def test_human_typing_empty_string(self):
        element = MagicMock()

        self.scraper._human_typing(element, "")

        element.send_keys.assert_not_called()

    # --------------------------------------------------
    # Random Human Action
    # --------------------------------------------------
    @patch("src.scraper.ActionChains")
    def test_random_human_action_executes(self, mock_chain):
        mock_chain.return_value = MagicMock()

        try:
            self.scraper._random_human_action()
        except Exception as e:
            self.fail(f"_random_human_action crashed: {e}")

    # --------------------------------------------------
    # Human Presence Wrapper
    # --------------------------------------------------
    @patch("src.scraper.ActionChains")
    def test_human_presence_executes(self, mock_chain):
        mock_chain.return_value = MagicMock()

        try:
            self.scraper._human_presence()
        except Exception as e:
            self.fail(f"_human_presence crashed: {e}")


if __name__ == "__main__":
    unittest.main()
