import unittest
from anthropic_vision_script import get_ramq

class TestRAMQProcessing(unittest.TestCase):
    """Test cases for RAMQ information extraction from GitHub images."""

    def setUp(self):
        """Set up test cases with sample URLs."""
        self.test_urls = [
            "https://i.ibb.co/7Jm0KvX/IMG-2618.jpg",
            "https://i.ibb.co/m92CFv2/IMG-2608.jpg",
            "https://i.ibb.co/3MdsCGv/IMG-2610.jpg", 
            "https://i.ibb.co/vV9MCcj/IMG-2611.jpg",
        ]

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
                self.assertIsInstance(dob, str)
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
                
                # Extract date from DOB string (assuming format YYYY-MM-DD)
                dob_parts = dob.split('-')
                self.assertEqual(len(dob_parts), 3)
                
                dob_year = int(dob_parts[0])
                dob_month = int(dob_parts[1])
                dob_day = int(dob_parts[2])
                
                # Check if the day and month match
                self.assertEqual(month, dob_month)
                self.assertEqual(day, dob_day)
                
                # Check if the year matches (considering century)
                self.assertEqual(dob_year % 100, year)

if __name__ == '__main__':
    unittest.main(verbosity=2) 