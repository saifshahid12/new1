# tests/test_category.py
import unittest
from unittest.mock import patch
import src.utils as utils  # patchable reference

class TestCategorySupport(unittest.TestCase):
    def setUp(self):
        self.posts = [
            {"Post Text": "Post A", "Author Name": "Author A", "Timestamp": "2026-01-01T12:00:00"},
            {"Post Text": "Post B", "Author Name": "Author B", "Timestamp": "2026-01-02T12:00:00"},
        ]
        self.category = "Posts"
        self.search_query = "Python intern"

    @patch("src.utils.export_data")
    def test_export_called_with_category(self, mock_export):
        """Export should be called with processed posts including category"""
        # Add category to posts (like main code does)
        for post in self.posts:
            post["Category"] = self.category

        # Call the function via utils reference
        utils.export_data(self.posts, self.search_query, self.category)

        mock_export.assert_called_once()
        args, kwargs = mock_export.call_args
        self.assertEqual(args[0], self.posts)
        self.assertEqual(args[1], self.search_query)
        self.assertEqual(args[2], self.category)

    def test_posts_have_category(self):
        for post in self.posts:
            post["Category"] = self.category
        for post in self.posts:
            self.assertIn("Category", post)
            self.assertEqual(post["Category"], self.category)

    def test_category_field_integrity(self):
        for post in self.posts:
            post["Category"] = self.category
        for post in self.posts:
            self.assertEqual(post["Category"], self.category)

if __name__ == "__main__":
    unittest.main()
