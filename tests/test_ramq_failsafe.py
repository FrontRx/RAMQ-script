import unittest
from datetime import datetime

from anthropic_vision_script import (
    normalize_ramq,
    parse_date_string,
    extract_birth_info_from_ramq,
)


class TestRamqFailsafeHelpers(unittest.TestCase):
    def test_normalize_ramq_handles_missing_or_messy_values(self):
        self.assertIsNone(normalize_ramq(None))
        self.assertEqual(normalize_ramq("abc d9001 0101"), "ABCD90010101")
        self.assertEqual(normalize_ramq("RAMQ: TREM64055089"), "TREM64055089")

    def test_parse_date_string_accepts_multiple_formats(self):
        self.assertEqual(parse_date_string("1935-10-09"), datetime(1935, 10, 9))
        self.assertEqual(parse_date_string("09/10/1935"), datetime(1935, 10, 9))
        self.assertIsNone(parse_date_string("not-a-date"))

    def test_extract_birth_info_from_ramq(self):
        dob, gender, is_valid = extract_birth_info_from_ramq("ABCD90010111")
        self.assertEqual(dob, datetime(1990, 1, 1))
        self.assertEqual(gender, "male")
        self.assertIsInstance(is_valid, bool)


if __name__ == "__main__":
    unittest.main()
