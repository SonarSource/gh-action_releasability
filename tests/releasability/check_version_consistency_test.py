import unittest
from unittest.mock import MagicMock

from releasability.checks.check_version_consistency import CheckVersionConsistency
from releasability.inline_check import CheckContext
from releasability.releasability_check_result import ReleasabilityCheckResult
from utils.artifactory_client import ArtifactoryClient


class TestCheckVersionConsistency(unittest.TestCase):

    def setUp(self):
        self.client = MagicMock()
        self.check = CheckVersionConsistency(artifactory_client=self.client)

    def test_check_name(self):
        self.assertEqual(self.check.name, "CheckVersionConsistency")

    def test_passes_when_input_matches_module_version(self):
        self.client.fetch_build_info.return_value = {
            'modules': [{'id': 'com.sonarsource.sonarqube:sonar-enterprise:2026.4.0.125719'}]
        }
        context = CheckContext(
            "SonarSource", "sonar-enterprise", "branch-2026.4",
            "sqs-2026.4.0.125719", "abc123",
        )

        result = self.check.execute(context)

        self.assertEqual(result.state, ReleasabilityCheckResult.CHECK_PASSED)
        self.client.fetch_build_info.assert_called_once_with("sonar-enterprise-sqs", 125719)

    def test_fails_when_patch_differs(self):
        self.client.fetch_build_info.return_value = {
            'modules': [{'id': 'com.sonarsource.sonarqube:sonar-enterprise:2026.4.1.125719'}]
        }
        context = CheckContext(
            "SonarSource", "sonar-enterprise", "branch-2026.4",
            "sqs-2026.4.0.125719", "abc123",
        )

        result = self.check.execute(context)

        self.assertEqual(result.state, ReleasabilityCheckResult.CHECK_FAILED)
        self.assertIn("2026.4.0", result.message)
        self.assertIn("2026.4.1", result.message)

    def test_fails_when_build_number_differs(self):
        self.client.fetch_build_info.return_value = {
            'modules': [{'id': 'org.sonarsource.demo:demo:1.2.3.200'}]
        }
        context = CheckContext("SonarSource", "demo", "master", "1.2.3.100", "abc123")

        result = self.check.execute(context)

        self.assertEqual(result.state, ReleasabilityCheckResult.CHECK_FAILED)
        self.assertIn("build number", result.message)

    def test_errors_when_no_modules(self):
        self.client.fetch_build_info.return_value = {'modules': []}
        context = CheckContext("SonarSource", "demo", "master", "1.2.3.100", "abc123")

        result = self.check.execute(context)

        self.assertEqual(result.state, ReleasabilityCheckResult.CHECK_ERROR)
        self.assertIn("no modules", result.message)

    def test_not_relevant_when_build_info_missing(self):
        self.client.fetch_build_info.side_effect = ArtifactoryClient.FetchError(
            'not found', status_code=404
        )
        context = CheckContext("SonarSource", "demo", "master", "1.2.3.100", "abc123")

        result = self.check.execute(context)

        self.assertEqual(result.state, ReleasabilityCheckResult.CHECK_NOT_RELEVANT)

    def test_errors_when_auth_fails(self):
        self.client.fetch_build_info.side_effect = ArtifactoryClient.FetchError(
            'unauthorized', status_code=401
        )
        context = CheckContext("SonarSource", "demo", "master", "1.2.3.100", "abc123")

        result = self.check.execute(context)

        self.assertEqual(result.state, ReleasabilityCheckResult.CHECK_ERROR)

    def test_does_not_treat_patch_digit_as_build_number(self):
        self.client.fetch_build_info.return_value = {
            'modules': [{'id': 'org.sonarsource.demo:demo:1.2.3'}]
        }
        context = CheckContext("SonarSource", "demo", "master", "1.2.3.100", "abc123")

        result = self.check.execute(context)

        # No trailing build on module version → skip build-number comparison → PASS on MMP
        self.assertEqual(result.state, ReleasabilityCheckResult.CHECK_PASSED)


if __name__ == '__main__':
    unittest.main()
