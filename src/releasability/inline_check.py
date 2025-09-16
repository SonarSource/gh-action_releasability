from abc import ABC, abstractmethod
from typing import Optional
from .releasability_check_result import ReleasabilityCheckResult


class CheckContext:
    """Context object containing information needed for check execution."""

    def __init__(self, organization: str, repository: str, branch: str, version: str, commit_sha: str):
        self.organization = organization
        self.repository = repository
        self.branch = branch
        self.version = version
        self.commit_sha = commit_sha

    def __str__(self) -> str:
        return f"{self.organization}/{self.repository}#{self.version}@{self.commit_sha}"


class InlineCheck(ABC):
    """Abstract base class for inline releasability checks."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of the check."""
        pass

    @abstractmethod
    def execute(self, context: CheckContext) -> ReleasabilityCheckResult:
        """
        Execute the check and return the result.

        Args:
            context: CheckContext containing repository and version information

        Returns:
            ReleasabilityCheckResult with the check outcome
        """
        pass

    def __str__(self) -> str:
        return f"InlineCheck({self.name})"
