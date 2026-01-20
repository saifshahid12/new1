import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import unittest
import csv
import json
from unittest.mock import patch
from src.utils import export_data, load_config


class TestTask08ExportCSV(unittest.TestCase):
    def setUp(self):
        self.test_data = [
            {
                "Post Text": "Post A",
                "Author Name": "Author A",
                "Timestamp": "1h",
                "Post URL": "url1",
                "Category": "Posts",
                "keyword_matched": True,
                "search_query": "Python intern"
            },
            {
                "Post Text": "Post B",
                "Author Name": "Author B",
                "Timestamp": "2h",
                "Post URL": "url2",
                "Category": "Videos",
                "keyword_matched": False,
                "search_query": "Python intern"
            }
        ]

        self.output_dir = os.path.join(os.path.dirname(__file__), "..", "output")
        os.makedirs(self.output_dir, exist_ok=True)

    def test_csv_creation(self):
        export_data(self.test_data, "Python_intern", "Posts")

        files = [f for f in os.listdir(self.output_dir) if f.endswith(".csv")]
        self.assertTrue(len(files) > 0)

        latest_csv = max(
            [os.path.join(self.output_dir, f) for f in files],
            key=os.path.getctime
        )

        with open(latest_csv, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for key in self.test_data[0].keys():
                self.assertIn(key, reader.fieldnames)

            rows = list(reader)
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["Post Text"], "Post A")
            self.assertEqual(rows[1]["keyword_matched"], "False")

    def test_json_creation(self):
        export_data(self.test_data, "Python_intern", "Posts")

        files = [f for f in os.listdir(self.output_dir) if f.endswith(".json")]
        self.assertTrue(len(files) > 0)

        latest_json = max(
            [os.path.join(self.output_dir, f) for f in files],
            key=os.path.getctime
        )

        with open(latest_json, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["Author Name"], "Author A")
        self.assertIn("keyword_matched", data[1])

    @patch("builtins.print")
    def test_export_no_exception(self, mock_print):
        try:
            export_data(self.test_data, "Python_intern", "Posts")
        except Exception as e:
            self.fail(f"export_data raised an exception {e}")


if __name__ == "__main__":
    unittest.main()
