import unittest
import os
from unittest.mock import patch, MagicMock

from releasability.checks.check_licenses import CheckLicenses
from releasability.inline_check import CheckContext
from releasability.releasability_check_result import ReleasabilityCheckResult


class TestCheckLicenses(unittest.TestCase):

    def setUp(self):
        # Clear any existing ARTIFACTORY_TOKEN to test without token
        if 'ARTIFACTORY_TOKEN' in os.environ:
            del os.environ['ARTIFACTORY_TOKEN']
        self.check = CheckLicenses()

    def test_check_name(self):
        """Test that the check has the correct name."""
        self.assertEqual(self.check.name, "CheckLicenses")

    def test_check_execution_without_token(self):
        """Test that the check fails when ARTIFACTORY_TOKEN is not set."""
        context = CheckContext("sonar", "sonar-dummy", "master", "1.0.0", "abc123")

        result = self.check.execute(context)

        self.assertEqual(result.name, "CheckLicenses")
        self.assertEqual(result.state, ReleasabilityCheckResult.CHECK_ERROR)
        self.assertIn("Artifactory not configured", result.message)
        self.assertFalse(result.passed)

    @patch('releasability.checks.check_licenses.Artifactory')
    def test_check_execution_with_token_success(self, mock_artifactory_class):
        """Test that the check passes when artifacts are downloaded successfully."""
        # Set up environment
        os.environ['ARTIFACTORY_TOKEN'] = 'test-token'

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

        # Create a new check instance to pick up the token
        check = CheckLicenses()

        context = CheckContext("sonar", "sonar-dummy", "master", "1.0.0", "abc123")
        result = check.execute(context)

        self.assertEqual(result.name, "CheckLicenses")
        self.assertEqual(result.state, ReleasabilityCheckResult.CHECK_PASSED)
        self.assertIn("downloaded 1 artifacts", result.message)
        self.assertIn("test-plugin-1.0.0.jar", result.message)
        self.assertTrue(result.passed)

    @patch('releasability.checks.check_licenses.Artifactory')
    def test_check_execution_with_token_no_artifacts(self, mock_artifactory_class):
        """Test that the check fails when no artifacts are found."""
        # Set up environment
        os.environ['ARTIFACTORY_TOKEN'] = 'test-token'

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
    def test_check_execution_with_token_exception(self, mock_artifactory_class):
        """Test that the check handles exceptions gracefully."""
        # Set up environment
        os.environ['ARTIFACTORY_TOKEN'] = 'test-token'

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

    def tearDown(self):
        """Clean up environment variables after each test."""
        if 'ARTIFACTORY_TOKEN' in os.environ:
            del os.environ['ARTIFACTORY_TOKEN']


if __name__ == '__main__':
    unittest.main()
