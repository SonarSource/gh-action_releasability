

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
        for key, value in self.details.items():
            if isinstance(value, list) and value:
                lines.append(f"{key}: {len(value)} items")
                for item in value[:5]:  # Show first 5 items
                    lines.append(f"  • {item}")
                if len(value) > 5:
                    lines.append(f"  ... and {len(value) - 5} more")
            elif value:
                lines.append(f"{key}: {value}")

        return '\n'.join(lines)

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
