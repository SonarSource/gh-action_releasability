import unittest
from unittest.mock import MagicMock, patch

from releasability.releasability_service import ReleasabilityService
from releasability.releasability_check_result import ReleasabilityCheckResult
from inline_check_test import MockInlineCheck


class TestReleasabilityServiceHybrid(unittest.TestCase):

    def setUp(self):
        with patch('boto3.Session'):
            self.service = ReleasabilityService()

    def test_register_inline_checks(self):
        """Test that inline checks are registered on initialization."""
        inline_checks = self.service.check_registry.get_inline_check_names()

        # Should have CheckLicenses registered
        self.assertIn("CheckLicenses", inline_checks)

    def test_execute_inline_checks(self):
        """Test executing inline checks."""
        # Add a mock check for testing
        mock_check = MockInlineCheck("TestCheck")
        self.service.check_registry.register_inline_check(mock_check)

        results = self.service.execute_inline_checks(
            "sonar", "sonar-dummy", "master", "1.0.0.123", "abc123"
        )

        # Should have results from both CheckLicenses and TestCheck
        self.assertEqual(len(results), 2)

        # Check that CheckLicenses result is present
        check_licenses_result = next(
            (r for r in results if r.name == "CheckLicenses"), None
        )
        self.assertIsNotNone(check_licenses_result)
        # CheckLicenses now returns CHECK_ERROR when ARTIFACTORY_TOKEN is not configured
        self.assertEqual(check_licenses_result.state, ReleasabilityCheckResult.CHECK_ERROR)

        # Check that TestCheck result is present
        test_check_result = next(
            (r for r in results if r.name == "TestCheck"), None
        )
        self.assertIsNotNone(test_check_result)
        self.assertEqual(test_check_result.state, ReleasabilityCheckResult.CHECK_PASSED)

    def test_execute_inline_checks_with_error(self):
        """Test that inline check errors are handled gracefully."""
        # Create a check that raises an exception
        class FailingCheck(MockInlineCheck):
            def execute(self, context):
                raise Exception("Test error")

        failing_check = FailingCheck("FailingCheck")
        self.service.check_registry.register_inline_check(failing_check)

        results = self.service.execute_inline_checks(
            "sonar", "sonar-dummy", "master", "1.0.0.123", "abc123"
        )

        # Should have results from CheckLicenses and FailingCheck
        self.assertEqual(len(results), 2)

        # Check that FailingCheck result has ERROR state
        failing_result = next(
            (r for r in results if r.name == "FailingCheck"), None
        )
        self.assertIsNotNone(failing_result)
        self.assertEqual(failing_result.state, ReleasabilityCheckResult.CHECK_ERROR)
        self.assertIn("Test error", failing_result.message)

    @patch('boto3.Session')
    def test_start_lambda_checks(self, mock_session):
        """Test starting lambda checks."""
        # Mock the SNS client
        mock_sns_client = MagicMock()
        mock_sns_client.publish.return_value = {'MessageId': 'test-message-id'}
        mock_session.return_value.client.return_value = mock_sns_client

        service = ReleasabilityService()

        correlation_id = service.start_lambda_checks(
            "sonar", "sonar-dummy", "master", "1.0.0.123", "abc123"
        )

        self.assertIsNotNone(correlation_id)
        self.assertIsInstance(correlation_id, str)
        mock_sns_client.publish.assert_called_once()

    def test_get_combined_report(self):
        """Test getting a combined report with inline and lambda results."""
        # Mock inline results
        inline_results = [
            ReleasabilityCheckResult("CheckLicenses", ReleasabilityCheckResult.CHECK_PASSED, "Inline result")
        ]

        # Mock lambda results
        lambda_results = [
            ReleasabilityCheckResult("CheckDependencies", ReleasabilityCheckResult.CHECK_PASSED, "Lambda result")
        ]

        with patch.object(self.service, 'get_lambda_check_results', return_value=lambda_results):
            report = self.service.get_combined_report("test-correlation-id", inline_results)

            all_checks = report.get_checks()
            self.assertEqual(len(all_checks), 2)

            # Check that both inline and lambda results are present
            check_names = [check.name for check in all_checks]
            self.assertIn("CheckLicenses", check_names)
            self.assertIn("CheckDependencies", check_names)

    @patch('boto3.Session')
    def test_start_releasability_checks_hybrid(self, mock_session):
        """Test the main hybrid entry point."""
        # Mock the SNS client
        mock_sns_client = MagicMock()
        mock_sns_client.publish.return_value = {'MessageId': 'test-message-id'}
        mock_session.return_value.client.return_value = mock_sns_client

        service = ReleasabilityService()

        correlation_id, inline_results = service.start_releasability_checks(
            "sonar", "sonar-dummy", "master", "1.0.0.123", "abc123"
        )

        # Should return correlation ID and inline results
        self.assertIsNotNone(correlation_id)
        self.assertIsInstance(inline_results, list)

        # Should have at least CheckLicenses result
        self.assertGreater(len(inline_results), 0)
        check_licenses_result = next(
            (r for r in inline_results if r.name == "CheckLicenses"), None
        )
        self.assertIsNotNone(check_licenses_result)


if __name__ == '__main__':
    unittest.main()
