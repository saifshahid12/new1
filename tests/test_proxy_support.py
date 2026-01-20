import unittest
from src.scraper import LinkedInScraper


class TestProxySupport(unittest.TestCase):

    def setUp(self):
        self.base_config = {
            "scraper_settings": {
                "base_url": "https://www.linkedin.com/login",
                "search_query": "Python intern",
                "scroll_limit": 1
            },
            "human_mimicry": {
                "typing_speed": (0.01, 0.02)
            }
        }

    def test_proxy_disabled(self):
        """
        Proxy disabled → Scraper initializes safely
        """
        config = self.base_config.copy()
        config["proxy"] = {"enabled": False}

        scraper = LinkedInScraper(config, init_driver=False)

        self.assertIsNotNone(scraper)
        self.assertFalse(scraper.config["proxy"]["enabled"])

    def test_proxy_enabled_with_config(self):
        """
        Proxy enabled with host/port → Config accepted
        """
        config = self.base_config.copy()
        config["proxy"] = {
            "enabled": True,
            "host": "5.42.206.146",
            "port": 8081
        }

        scraper = LinkedInScraper(config, init_driver=False)

        self.assertTrue(scraper.config["proxy"]["enabled"])
        self.assertEqual(scraper.config["proxy"]["host"], "5.42.206.146")
        self.assertEqual(scraper.config["proxy"]["port"], 8081)

    def test_proxy_enabled_missing_host_port(self):
        """
        Proxy enabled but host/port missing → Should not crash
        """
        config = self.base_config.copy()
        config["proxy"] = {"enabled": True}

        scraper = LinkedInScraper(config, init_driver=False)

        self.assertIsNotNone(scraper)


if __name__ == "__main__":
    unittest.main()
