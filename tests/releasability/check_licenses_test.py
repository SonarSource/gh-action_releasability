import unittest

from releasability.checks.check_licenses import CheckLicenses
from releasability.inline_check import CheckContext
from releasability.releasability_check_result import ReleasabilityCheckResult


class TestCheckLicenses(unittest.TestCase):

    def setUp(self):
        self.check = CheckLicenses()

    def test_check_name(self):
        """Test that the check has the correct name."""
        self.assertEqual(self.check.name, "CheckLicenses")

    def test_check_execution_passes(self):
        """Test that the check currently passes (placeholder implementation)."""
        context = CheckContext("sonar", "sonar-dummy", "master", "1.0.0", "abc123")

        result = self.check.execute(context)

        self.assertEqual(result.name, "CheckLicenses")
        self.assertEqual(result.state, ReleasabilityCheckResult.CHECK_PASSED)
        self.assertIn("placeholder implementation", result.message)
        self.assertTrue(result.passed)

    def test_check_execution_with_different_context(self):
        """Test that the check works with different context values."""
        context = CheckContext("testorg", "testrepo", "feature-branch", "2.1.0", "def456")

        result = self.check.execute(context)

        self.assertEqual(result.name, "CheckLicenses")
        self.assertEqual(result.state, ReleasabilityCheckResult.CHECK_PASSED)
        self.assertIn("testrepo", result.message)
        self.assertTrue(result.passed)

    def test_check_string_representation(self):
        """Test the string representation of the check."""
        expected = "InlineCheck(CheckLicenses)"
        self.assertEqual(str(self.check), expected)


if __name__ == '__main__':
    unittest.main()
