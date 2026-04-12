"""Tests for stealth module."""

import unittest
from unittest.mock import Mock, call
from trogocytosis.stealth import random_ua, patches, apply


class TestStealth(unittest.TestCase):
    """Tests for stealth functions."""

    def test_random_ua_returns_string(self):
        """Test that random_ua returns a non-empty string from the list."""
        ua = random_ua()
        self.assertIsInstance(ua, str)
        self.assertGreater(len(ua), 0)
        self.assertIn("Chrome", ua)
        self.assertIn("Mozilla", ua)

    def test_random_ua_is_random(self):
        """Test that random_ua returns different values occasionally (statistical test)."""
        # Get multiple UAs and check they're not all the same
        user_agents = {random_ua() for _ in range(10)}
        self.assertGreater(len(user_agents), 1)

    def test_patches_returns_non_empty_list(self):
        """Test that patches returns a list of JS patch strings."""
        js_patches = patches()
        self.assertIsInstance(js_patches, list)
        self.assertEqual(len(js_patches), 5)
        for js in js_patches:
            self.assertIsInstance(js, str)
            self.assertGreater(len(js), 0)

    def test_patches_contain_expected_content(self):
        """Test that patches contain the expected stealth patches."""
        js_patches = patches()
        # Check that webdriver patch is present
        self.assertTrue(any("webdriver" in js for js in js_patches))
        # Check that window.chrome patch is present
        self.assertTrue(any("window.chrome" in js for js in js_patches))
        # Check that plugins patch is present
        self.assertTrue(any("plugins" in js for js in js_patches))
        # Check that permissions query patch is present
        self.assertTrue(any("permissions.query" in js for js in js_patches))

    def test_apply_calls_evaluate_fn_for_all_patches(self):
        """Test that apply calls evaluate_fn for each patch."""
        mock_evaluate = Mock()
        apply(mock_evaluate)
        
        # Should call once for each patch from patches()
        expected_calls = [call(js) for js in patches()]
        mock_evaluate.assert_has_calls(expected_calls, any_order=True)
        self.assertEqual(mock_evaluate.call_count, len(patches()))


if __name__ == "__main__":
    unittest.main()
