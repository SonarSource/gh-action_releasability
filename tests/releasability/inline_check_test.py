import unittest
from unittest.mock import MagicMock, patch

from releasability.inline_check import CheckContext, InlineCheck
from releasability.releasability_check_result import ReleasabilityCheckResult


class MockInlineCheck(InlineCheck):
    """Mock inline check for testing."""

    def __init__(self, name: str, result_state: str = ReleasabilityCheckResult.CHECK_PASSED):
        self._name = name
        self._result_state = result_state

    @property
    def name(self) -> str:
        return self._name

    def execute(self, context: CheckContext) -> ReleasabilityCheckResult:
        return ReleasabilityCheckResult(
            self.name,
            self._result_state,
            f"Mock result for {context.repository}"
        )


class TestCheckContext(unittest.TestCase):

    def test_check_context_creation(self):
        context = CheckContext("sonar", "sonar-dummy", "master", "1.0.0", "abc123")

        self.assertEqual(context.organization, "sonar")
        self.assertEqual(context.repository, "sonar-dummy")
        self.assertEqual(context.branch, "master")
        self.assertEqual(context.version, "1.0.0")
        self.assertEqual(context.commit_sha, "abc123")

    def test_check_context_string_representation(self):
        context = CheckContext("sonar", "sonar-dummy", "master", "1.0.0", "abc123")
        expected = "sonar/sonar-dummy#1.0.0@abc123"

        self.assertEqual(str(context), expected)


class TestInlineCheck(unittest.TestCase):

    def test_mock_inline_check_execution(self):
        check = MockInlineCheck("TestCheck")
        context = CheckContext("sonar", "sonar-dummy", "master", "1.0.0", "abc123")

        result = check.execute(context)

        self.assertEqual(result.name, "TestCheck")
        self.assertEqual(result.state, ReleasabilityCheckResult.CHECK_PASSED)
        self.assertEqual(result.message, "Mock result for sonar-dummy")

    def test_mock_inline_check_with_failure(self):
        check = MockInlineCheck("TestCheck", ReleasabilityCheckResult.CHECK_FAILED)
        context = CheckContext("sonar", "sonar-dummy", "master", "1.0.0", "abc123")

        result = check.execute(context)

        self.assertEqual(result.name, "TestCheck")
        self.assertEqual(result.state, ReleasabilityCheckResult.CHECK_FAILED)
        self.assertFalse(result.passed)

    def test_inline_check_string_representation(self):
        check = MockInlineCheck("TestCheck")
        expected = "InlineCheck(TestCheck)"

        self.assertEqual(str(check), expected)


if __name__ == '__main__':
    unittest.main()
