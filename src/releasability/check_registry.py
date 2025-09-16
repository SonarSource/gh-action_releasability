from typing import Dict, Set, Type
from .inline_check import InlineCheck


class CheckRegistry:
    """Registry for managing both inline and lambda-based checks."""

    def __init__(self):
        # Lambda checks (existing)
        self.lambda_checks: Set[str] = {
            "CheckDependencies",
            "QA",
            "Jira",
            "CheckPeacheeLanguagesStatistics",
            "QualityGate",
            "ParentPOM",
            "GitHub",
            "CheckManifestValues",
        }

        # Inline checks registry
        self.inline_checks: Dict[str, InlineCheck] = {}

    def register_inline_check(self, check: InlineCheck) -> None:
        """
        Register an inline check.

        Args:
            check: InlineCheck instance to register
        """
        self.inline_checks[check.name] = check

    def get_inline_check(self, name: str) -> InlineCheck:
        """
        Get an inline check by name.

        Args:
            name: Name of the check

        Returns:
            InlineCheck instance

        Raises:
            KeyError: If check is not found
        """
        return self.inline_checks[name]

    def get_all_check_names(self) -> Set[str]:
        """Get all check names (both inline and lambda)."""
        return self.lambda_checks | set(self.inline_checks.keys())

    def get_inline_check_names(self) -> Set[str]:
        """Get only inline check names."""
        return set(self.inline_checks.keys())

    def get_lambda_check_names(self) -> Set[str]:
        """Get only lambda check names."""
        return self.lambda_checks.copy()

    def is_inline_check(self, name: str) -> bool:
        """Check if a check name is an inline check."""
        return name in self.inline_checks

    def is_lambda_check(self, name: str) -> bool:
        """Check if a check name is a lambda check."""
        return name in self.lambda_checks
