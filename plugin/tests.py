import sys
sys.path.append("src")

import dialog
from dialog import sanitize_template_name
import logging
import unittest


class TestDialog(unittest.TestCase):
    def setUp(self):
        """Characters except for A-Z, a-z, 0-9, -, +, _ and ' ' will be ignored."""
        self.allowed = ['-','_','+',' '] + [chr(i) for i in range(128) if chr(i).isalnum()]
        self.disallowed = [chr(i) for i in range(256) if chr(i) not in self.allowed]


    def test_sanitize_template_name_spaces_allowed(self):
        name = "Hello World Hello"
        self.assertEqual("Hello World Hello", sanitize_template_name(name))

    def test_sanitize_template_name_special_chars_exceptions(self):
        name = "Hello{}World{}Hello"

        for ch in self.allowed:
            value = name.format(ch, ch)
            expected = value
            self.assertEqual(expected, sanitize_template_name(value))

    def test_sanitize_template_name_special_chars(self):
        name = "Hello{}World{}Hello"

        for ch in self.disallowed:
            expected = name.format("", "")
            value = name.format(ch, ch)
            self.assertEqual(expected, sanitize_template_name(value))



if __name__ == "__main__":
    unittest.main()
