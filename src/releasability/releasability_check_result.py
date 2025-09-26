

class ReleasabilityCheckResult:
    CHECK_OPTIONAL_PREFIX = "\u2713"
    SUCCESS_PREFIX = "\u2705"
    FAILURE_PREFIX = "\u274c"
    UNKNOWN_PREFIX = "\u2753"

    CHECK_PASSED = 'PASSED'
    CHECK_NOT_RELEVANT = 'NOT_RELEVANT'
    CHECK_ERROR = 'ERROR'
    CHECK_FAILED = 'FAILED'

    name: str
    state: str
    passed: bool
    message: str
    details: dict

    def __init__(self, name: str, state: str, message: str = None, details: dict = None):
        self.name = name
        self.state = state
        self.message = message
        self.details = details or {}
        self.passed = self.has_passed(state)

    def __str__(self):
        prefix = self._get_prefix()

        note = ''
        if self.message is not None:
            note = f' - {self.message}'

        # Add detailed information if available
        if self.details:
            details_str = self._format_details()
            if details_str:
                note += f'\n{details_str}'

        return f'{prefix} {self.name} {note}'

    def _format_details(self) -> str:
        """Format detailed information for display."""
        if not self.details:
            return ''

        lines = []
        self._add_artifact_info(lines)
        self._add_missing_licenses(lines)
        self._add_license_mismatches(lines)
        self._add_sbom_coverage(lines)

        return '\n'.join(lines)

    def _add_artifact_info(self, lines: list) -> None:
        """Add artifact information to lines."""
        if 'artifacts' not in self.details:
            return

        artifacts = self.details['artifacts']
        lines.append(f"📦 Downloaded Artifacts ({len(artifacts)}):")
        for artifact in artifacts:
            size_mb = artifact.get('size', 0) / (1024 * 1024)
            lines.append(f"  • {artifact.get('name', 'Unknown')} ({size_mb:.1f} MB)")

    def _add_missing_licenses(self, lines: list) -> None:
        """Add missing licenses information to lines."""
        if 'missing_licenses' not in self.details or not self.details['missing_licenses']:
            return

        missing = self.details['missing_licenses']
        lines.append(f"❌ Missing Licenses ({len(missing)}):")
        self._add_limited_list(lines, missing, 10)

    def _add_license_mismatches(self, lines: list) -> None:
        """Add license mismatches information to lines."""
        if 'license_mismatches' not in self.details or not self.details['license_mismatches']:
            return

        mismatches = self.details['license_mismatches']
        lines.append(f"⚠️  License Mismatches ({len(mismatches)}):")
        self._add_limited_list(lines, mismatches, 10)

    def _add_sbom_coverage(self, lines: list) -> None:
        """Add SBOM coverage information to lines."""
        if 'sbom_coverage' not in self.details:
            return

        coverage = self.details['sbom_coverage']
        lines.append(f"📊 SBOM Coverage: {coverage:.1f}%")

    def _add_limited_list(self, lines: list, items: list, limit: int) -> None:
        """Add a limited list of items to lines."""
        for item in items[:limit]:
            lines.append(f"  • {item}")
        if len(items) > limit:
            lines.append(f"  ... and {len(items) - limit} more")

    def _get_prefix(self):
        match self.state:
            case self.CHECK_PASSED:
                return self.SUCCESS_PREFIX
            case self.CHECK_NOT_RELEVANT:
                return self.CHECK_OPTIONAL_PREFIX
            case self.CHECK_FAILED:
                return self.FAILURE_PREFIX
            case self.CHECK_ERROR:
                return self.FAILURE_PREFIX
            case _:
                return self.UNKNOWN_PREFIX

    def has_passed(self, state: str) -> bool:
        match state:
            case self.CHECK_PASSED:
                return True
            case self.CHECK_NOT_RELEVANT:
                return True
            case self.CHECK_FAILED:
                return False
            case self.CHECK_ERROR:
                return False
            case _:
                return False
