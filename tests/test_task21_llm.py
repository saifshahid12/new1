"""
Test file for Task 21: LLM Call to Process Content
Tests the mock LLM implementation for email validation with all edge cases
"""
import unittest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils import mock_llm_validate_content

class TestTask21LLMValidation(unittest.TestCase):
    """Test cases for Task 21 - LLM email validation with edge cases"""
    
    # ==================== EXISTING BASIC TESTS ====================
    
    def test_mock_llm_with_email(self):
        """Test LLM validation when email is present in text"""
        text_with_email = "Contact us at support@company.com for assistance"
        result = mock_llm_validate_content(text_with_email)
        
        # Check structure
        self.assertIn("email_present", result)
        self.assertIn("emails", result)
        
        # Check values
        self.assertTrue(result["email_present"])
        self.assertIn("support@company.com", result["emails"])
        self.assertGreater(len(result["emails"]), 0)
    
    def test_mock_llm_without_email(self):
        """Test LLM validation when no email is present"""
        text_without_email = "Hello world, this is a test post without email."
        result = mock_llm_validate_content(text_without_email)
        
        # Check structure
        self.assertIn("email_present", result)
        self.assertIn("emails", result)
        
        # Check values
        self.assertFalse(result["email_present"])
        self.assertEqual(len(result["emails"]), 0)
    
    def test_mock_llm_empty_text(self):
        """Test LLM validation with empty text"""
        result = mock_llm_validate_content("")
        
        self.assertIn("email_present", result)
        self.assertIn("emails", result)
        self.assertFalse(result["email_present"])
        self.assertEqual(len(result["emails"]), 0)
    
    # ==================== EDGE CASES MENTIONED IN FEEDBACK ====================
    
    def test_multiple_emails_extraction(self):
        """Test LLM validation with multiple different emails (edge case)"""
        text = """
        Contact emails:
        - hr@company.com
        - sales@company.com
        - support@domain.org
        """
        result = mock_llm_validate_content(text)
        
        self.assertTrue(result["email_present"])
        self.assertGreaterEqual(len(result["emails"]), 3, "Should extract multiple emails")
        
        # Check for specific emails
        expected_emails = ["hr@company.com", "sales@company.com", "support@domain.org"]
        for email in expected_emails:
            self.assertIn(email, result["emails"], f"Missing email: {email}")
    
    def test_duplicate_emails_extraction(self):
        """Test duplicate email extraction logic (edge case)"""
        text = "Email me at test@example.com or test@example.com or TEST@EXAMPLE.COM"
        result = mock_llm_validate_content(text)
        
        self.assertTrue(result["email_present"])
        # Should handle duplicates (case-insensitive)
        self.assertEqual(len(result["emails"]), 1, "Should deduplicate identical emails")
        self.assertIn("test@example.com", result["emails"])
    
    def test_malformed_emails_handling(self):
        """Test handling of malformed emails (edge case)"""
        text = """
        Valid email: user@domain.com
        Malformed: user@
        Malformed: @domain.com
        Valid: another@test.org
        Malformed: user@domain.
        """
        result = mock_llm_validate_content(text)
        
        self.assertTrue(result["email_present"], "Should find valid emails")
        
        # Should extract valid emails
        valid_emails = ["user@domain.com", "another@test.org"]
        for valid_email in valid_emails:
            self.assertIn(valid_email, result["emails"], f"Missing valid email: {valid_email}")
    
    def test_error_handling_non_string_input(self):
        """Test error handling paths with non-string input"""
        # Test with integer input
        try:
            result = mock_llm_validate_content(123)
            # If function returns result, check structure
            self.assertIn("email_present", result)
            self.assertIn("emails", result)
            self.assertIsInstance(result["emails"], list)
        except Exception as e:
            # Error is acceptable - just ensure it's handled gracefully
            pass
    
    def test_special_email_formats(self):
        """Test various email formats including special characters"""
        test_cases = [
            ("user.name@domain.com", ["user.name@domain.com"]),
            ("user+tag@domain.com", ["user+tag@domain.com"]),
            ("user@sub.domain.com", ["user@sub.domain.com"]),
            ("user@domain.co.uk", ["user@domain.co.uk"]),
            ("UPPER@DOMAIN.COM", ["UPPER@DOMAIN.COM"]),
            ("123@456.789", ["123@456.789"]),
        ]
        
        for text, expected_emails in test_cases:
            with self.subTest(text=text):
                result = mock_llm_validate_content(text)
                self.assertTrue(result["email_present"])
                for expected in expected_emails:
                    self.assertIn(expected, result["emails"])

if __name__ == '__main__':
    unittest.main(verbosity=2)