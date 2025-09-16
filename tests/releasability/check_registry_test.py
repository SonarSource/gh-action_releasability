import unittest

from releasability.check_registry import CheckRegistry
from inline_check_test import MockInlineCheck


class TestCheckRegistry(unittest.TestCase):

    def setUp(self):
        self.registry = CheckRegistry()

    def test_initial_lambda_checks(self):
        """Test that lambda checks are properly initialized."""
        lambda_checks = self.registry.get_lambda_check_names()

        self.assertIn("CheckDependencies", lambda_checks)
        self.assertIn("QA", lambda_checks)
        self.assertIn("Jira", lambda_checks)
        self.assertIn("CheckPeacheeLanguagesStatistics", lambda_checks)
        self.assertIn("QualityGate", lambda_checks)
        self.assertIn("ParentPOM", lambda_checks)
        self.assertIn("GitHub", lambda_checks)
        self.assertIn("CheckManifestValues", lambda_checks)

    def test_initial_inline_checks_empty(self):
        """Test that inline checks start empty."""
        inline_checks = self.registry.get_inline_check_names()

        self.assertEqual(len(inline_checks), 0)

    def test_register_inline_check(self):
        """Test registering an inline check."""
        check = MockInlineCheck("TestCheck")

        self.registry.register_inline_check(check)

        self.assertIn("TestCheck", self.registry.get_inline_check_names())
        self.assertEqual(self.registry.get_inline_check("TestCheck"), check)

    def test_get_all_check_names(self):
        """Test getting all check names (both inline and lambda)."""
        check = MockInlineCheck("TestCheck")
        self.registry.register_inline_check(check)

        all_checks = self.registry.get_all_check_names()

        # Should contain both lambda and inline checks
        self.assertIn("CheckDependencies", all_checks)  # Lambda check
        self.assertIn("TestCheck", all_checks)  # Inline check

    def test_is_inline_check(self):
        """Test checking if a check is an inline check."""
        check = MockInlineCheck("TestCheck")
        self.registry.register_inline_check(check)

        self.assertTrue(self.registry.is_inline_check("TestCheck"))
        self.assertFalse(self.registry.is_inline_check("CheckDependencies"))
        self.assertFalse(self.registry.is_inline_check("NonExistentCheck"))

    def test_is_lambda_check(self):
        """Test checking if a check is a lambda check."""
        self.assertTrue(self.registry.is_lambda_check("CheckDependencies"))
        self.assertFalse(self.registry.is_lambda_check("TestCheck"))
        self.assertFalse(self.registry.is_lambda_check("NonExistentCheck"))

    def test_get_nonexistent_inline_check_raises_keyerror(self):
        """Test that getting a non-existent inline check raises KeyError."""
        with self.assertRaises(KeyError):
            self.registry.get_inline_check("NonExistentCheck")


if __name__ == '__main__':
    unittest.main()
