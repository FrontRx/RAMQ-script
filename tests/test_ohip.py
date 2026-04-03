import unittest

from anthropic_vision_script import normalize_ohip, validate_ohip


class TestNormalizeOhip(unittest.TestCase):
    def test_valid_10_digits(self):
        result = normalize_ohip("1234567890")
        self.assertEqual(result, {"number": "1234567890", "version_code": None})

    def test_valid_10_digits_with_version_code(self):
        result = normalize_ohip("1234567890AB")
        self.assertEqual(result, {"number": "1234567890", "version_code": "AB"})

    def test_strips_spaces(self):
        result = normalize_ohip("1234 5678 90AB")
        self.assertEqual(result, {"number": "1234567890", "version_code": "AB"})

    def test_strips_dashes(self):
        result = normalize_ohip("1234-567-890-AB")
        self.assertEqual(result, {"number": "1234567890", "version_code": "AB"})

    def test_strips_mixed_whitespace_and_dashes(self):
        result = normalize_ohip("1234 567-890 AB")
        self.assertEqual(result, {"number": "1234567890", "version_code": "AB"})

    def test_lowercase_version_code(self):
        result = normalize_ohip("1234567890ab")
        self.assertEqual(result, {"number": "1234567890", "version_code": "AB"})

    def test_none_input(self):
        self.assertIsNone(normalize_ohip(None))

    def test_empty_string(self):
        self.assertIsNone(normalize_ohip(""))

    def test_9_digits_invalid(self):
        self.assertIsNone(normalize_ohip("123456789"))

    def test_11_digits_invalid(self):
        self.assertIsNone(normalize_ohip("12345678901"))

    def test_all_letters_invalid(self):
        self.assertIsNone(normalize_ohip("ABCDEFGHIJ"))

    def test_1_letter_version_code_invalid(self):
        self.assertIsNone(normalize_ohip("1234567890A"))

    def test_3_letter_version_code_invalid(self):
        self.assertIsNone(normalize_ohip("1234567890ABC"))


class TestValidateOhip(unittest.TestCase):
    def test_valid_10_digits(self):
        self.assertTrue(validate_ohip("1234567890"))

    def test_valid_with_version_code(self):
        self.assertTrue(validate_ohip("1234567890AB"))

    def test_valid_with_spaces(self):
        self.assertTrue(validate_ohip("1234 567 890"))

    def test_valid_with_dashes(self):
        self.assertTrue(validate_ohip("1234-567890-AB"))

    def test_invalid_9_digits(self):
        self.assertFalse(validate_ohip("123456789"))

    def test_invalid_all_letters(self):
        self.assertFalse(validate_ohip("ABCDEFGHIJ"))

    def test_invalid_11_digits(self):
        self.assertFalse(validate_ohip("12345678901"))

    def test_invalid_1_letter_version(self):
        self.assertFalse(validate_ohip("1234567890A"))


if __name__ == "__main__":
    unittest.main()
