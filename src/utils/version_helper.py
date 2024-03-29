class VersionHelper:

    @staticmethod
    def extract_build_number(version) -> int:
        parts = version.split('.')
        if len(parts) != 4:
            raise ValueError(f'The provided version {version}  does not match the standardized format '
                             f'used commonly across the organization: <MAJOR>.<MINOR>.<PATCH>.<BUILD NUMBER>')

        return int(parts[3])

    @staticmethod
    def extract_semantic_version(version) -> str:
        parts = version.split('.')
        if len(parts) < 3:
            raise ValueError(f'The provided version {version}  does not follow semantic versioning '
                             f'(at least 3 parts are required <MAJOR>.<MINOR>.<PATCH>)')

        return f'{parts[0]}.{parts[1]}.{parts[2]}'

    @staticmethod
    def is_valid_sonar_version(version: str) -> bool:
        if "." not in version:
            return False
        parts = version.split('.')
        if len(parts) != 4:
            return False

        return True
