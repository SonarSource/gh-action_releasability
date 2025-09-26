import unittest
import os
from unittest.mock import patch, MagicMock

from releasability.checks.check_licenses import CheckLicenses
from releasability.inline_check import CheckContext
from releasability.releasability_check_result import ReleasabilityCheckResult


class TestCheckLicenses(unittest.TestCase):

    def setUp(self):
        self.check = CheckLicenses()

    def test_check_name(self):
        """Test that the check has the correct name."""
        self.assertEqual(self.check.name, "CheckLicenses")

    @patch.dict(os.environ, {'SONAR_PROJECT_KEY': 'test-project-key'}, clear=False)
    def test_check_execution_without_token(self):
        """Test that the check fails when ARTIFACTORY_TOKEN is not set."""
        context = CheckContext("sonar", "sonar-dummy", "master", "1.0.0", "abc123")

        result = self.check.execute(context)

        self.assertEqual(result.name, "CheckLicenses")
        self.assertEqual(result.state, ReleasabilityCheckResult.CHECK_ERROR)
        self.assertIn("Artifactory not configured", result.message)
        self.assertFalse(result.passed)

    @patch('releasability.checks.check_licenses.Artifactory')
    @patch('releasability.checks.check_licenses.LPSValidator')
    @patch.dict(os.environ, {'ARTIFACTORY_TOKEN': 'test-token', 'SONAR_PROJECT_KEY': 'test-project-key'}, clear=False)
    def test_check_execution_with_token_success(self, mock_lps_validator_class, mock_artifactory_class):
        """Test that the check passes when artifacts are downloaded successfully."""

        # Mock the Artifactory instance
        mock_artifactory = MagicMock()
        mock_artifactory_class.return_value = mock_artifactory

        # Mock successful artifact download
        mock_artifacts = [
            {
                'name': 'test-plugin-1.0.0.jar',
                'path': '/tmp/test-plugin-1.0.0.jar',
                'group_id': 'org.sonarsource',
                'artifact_id': 'test-plugin',
                'version': '1.0.0',
                'extension': 'jar',
                'classifier': None
            }
        ]
        mock_artifactory.download_artifacts_from_build_info.return_value = mock_artifacts

        # Mock LPS validator
        mock_lps_validator = MagicMock()
        mock_lps_validator_class.return_value = mock_lps_validator
        mock_lps_validator.validate_artifacts.return_value = {
            'lps_compliant': True,
            'artifacts_processed': 1,
            'licenses_extracted': {'test-plugin-1.0.0.jar': []},
            'sbom_comparison': {'coverage_percentage': 100.0},
            'issues': []
        }

        # Create a new check instance to pick up the token
        check = CheckLicenses()

        context = CheckContext("sonar", "sonar-dummy", "master", "1.0.0", "abc123")
        result = check.execute(context)

        self.assertEqual(result.name, "CheckLicenses")
        self.assertEqual(result.state, ReleasabilityCheckResult.CHECK_PASSED)
        self.assertIn("LPS validation passed", result.message)
        self.assertTrue(result.passed)

    @patch('releasability.checks.check_licenses.Artifactory')
    @patch.dict(os.environ, {'ARTIFACTORY_TOKEN': 'test-token', 'SONAR_PROJECT_KEY': 'test-project-key'}, clear=False)
    def test_check_execution_with_token_no_artifacts(self, mock_artifactory_class):
        """Test that the check fails when no artifacts are found."""

        # Mock the Artifactory instance
        mock_artifactory = MagicMock()
        mock_artifactory_class.return_value = mock_artifactory

        # Mock empty artifact list
        mock_artifactory.download_artifacts_from_build_info.return_value = []

        # Create a new check instance to pick up the token
        check = CheckLicenses()

        context = CheckContext("sonar", "sonar-dummy", "master", "1.0.0", "abc123")
        result = check.execute(context)

        self.assertEqual(result.name, "CheckLicenses")
        self.assertEqual(result.state, ReleasabilityCheckResult.CHECK_FAILED)
        self.assertIn("No artifacts found", result.message)
        self.assertFalse(result.passed)

    @patch('releasability.checks.check_licenses.Artifactory')
    @patch.dict(os.environ, {'ARTIFACTORY_TOKEN': 'test-token', 'SONAR_PROJECT_KEY': 'test-project-key'}, clear=False)
    def test_check_execution_with_token_exception(self, mock_artifactory_class):
        """Test that the check handles exceptions gracefully."""

        # Mock the Artifactory instance
        mock_artifactory = MagicMock()
        mock_artifactory_class.return_value = mock_artifactory

        # Mock exception during download
        mock_artifactory.download_artifacts_from_build_info.side_effect = Exception("Download failed")

        # Create a new check instance to pick up the token
        check = CheckLicenses()

        context = CheckContext("sonar", "sonar-dummy", "master", "1.0.0", "abc123")
        result = check.execute(context)

        self.assertEqual(result.name, "CheckLicenses")
        self.assertEqual(result.state, ReleasabilityCheckResult.CHECK_ERROR)
        self.assertIn("License check error", result.message)
        self.assertIn("Download failed", result.message)
        self.assertFalse(result.passed)

    def test_check_string_representation(self):
        """Test the string representation of the check."""
        expected = "InlineCheck(CheckLicenses)"
        self.assertEqual(str(self.check), expected)

    @patch.dict(os.environ, {}, clear=True)
    def test_execute_bypasses_when_sonar_project_key_not_set(self):
        """Test that the check bypasses when SONAR_PROJECT_KEY is not set."""
        context = CheckContext("sonar", "sonar-dummy", "master", "1.0.0.123", "abc123")
        result = self.check.execute(context)

        self.assertEqual(result.name, "CheckLicenses")
        self.assertEqual(result.state, ReleasabilityCheckResult.CHECK_PASSED)
        self.assertIn("bypassed", result.message)
        self.assertIn("SONAR_PROJECT_KEY not configured", result.message)

    @patch.dict(os.environ, {'SONAR_PROJECT_KEY': ''}, clear=False)
    def test_execute_bypasses_when_sonar_project_key_empty(self):
        """Test that the check bypasses when SONAR_PROJECT_KEY is empty."""
        context = CheckContext("sonar", "sonar-dummy", "master", "1.0.0.123", "abc123")
        result = self.check.execute(context)

        self.assertEqual(result.name, "CheckLicenses")
        self.assertEqual(result.state, ReleasabilityCheckResult.CHECK_PASSED)
        self.assertIn("bypassed", result.message)
        self.assertIn("SONAR_PROJECT_KEY not configured", result.message)


if __name__ == '__main__':
    unittest.main()
