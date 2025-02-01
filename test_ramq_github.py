import unittest
from datetime import datetime
from anthropic_vision_script import get_ramq
import httpx

class TestRAMQProcessing(unittest.TestCase):
    """Test cases for RAMQ information extraction from GitHub images."""

    def setUp(self):
        """Set up test cases with sample URLs."""
        self.test_urls = [
            "https://i.ibb.co/7Jm0KvX/IMG-2618.jpg",
        ]
        self.timeout = httpx.Timeout(30.0, connect=30.0)
        self.client = httpx.Client(timeout=self.timeout)

    def tearDown(self):
        """Clean up resources."""
        self.client.close()

    def test_ramq_format(self):
        """Test if RAMQ numbers follow the correct format (4 letters + 8 digits)."""
        for url in self.test_urls:
            with self.subTest(url=url):
                result = get_ramq(url, is_image=True)
                self.assertIsInstance(result, tuple)
                self.assertEqual(len(result), 6)
                ramq = result[0]
                self.assertRegex(ramq, r'^[A-Z]{4}\d{8}$')

    def test_result_structure(self):
        """Test if the result tuple contains all required fields."""
        for url in self.test_urls:
            with self.subTest(url=url):
                result = get_ramq(url, is_image=True)
                ramq, last_name, first_name, dob, gender, is_valid = result
                
                # Check types
                self.assertIsInstance(ramq, str)
                self.assertIsInstance(last_name, str)
                self.assertIsInstance(first_name, str)
                self.assertIsInstance(dob, datetime)  # Changed from str to datetime
                self.assertIsInstance(gender, str)
                self.assertIsInstance(is_valid, bool)

    def test_gender_validation(self):
        """Test if gender is correctly extracted from RAMQ."""
        for url in self.test_urls:
            with self.subTest(url=url):
                result = get_ramq(url, is_image=True)
                ramq, _, _, _, gender, _ = result
                
                # Check if month indicates correct gender
                month_digit = int(ramq[6])
                if month_digit in [5, 6]:
                    self.assertEqual(gender.lower(), "female")
                else:
                    self.assertEqual(gender.lower(), "male")

    def test_date_validation(self):
        """Test if date of birth is valid and matches RAMQ."""
        for url in self.test_urls:
            with self.subTest(url=url):
                result = get_ramq(url, is_image=True)
                ramq, _, _, dob, _, _ = result
                
                # Extract date components from RAMQ
                year = int(ramq[4:6])
                month = int(ramq[6:8]) % 50  # Adjust for gender encoding
                day = int(ramq[8:10])
                
                # Get date components from datetime object
                dob_year = dob.year
                dob_month = dob.month
                dob_day = dob.day
                
                # Check if the day and month match
                self.assertEqual(month, dob_month)
                self.assertEqual(day, dob_day)
                
                # Check if the year matches (considering century)
                self.assertEqual(dob_year % 100, year)

if __name__ == '__main__':
    unittest.main(verbosity=2) 