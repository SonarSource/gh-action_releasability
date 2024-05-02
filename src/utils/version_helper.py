import re


class VersionHelper:
    VERSION_NUMBER_PLUS_SIGN_REGEX = r"^(\d+)\.(\d+)\.(\d+)\+(\d+)$"

    @staticmethod
    def extract_build_number(version) -> int:
        if not VersionHelper.is_valid_version(version):
            raise ValueError(f'The provided version {version}  does not match the standardized format '
                             f'used commonly across the organization: <MAJOR>.<MINOR>.<PATCH>.<BUILD NUMBER>')

        parts = VersionHelper._sanitize_version(version).split('.')
        if len(parts) != 4:
            raise ValueError(f'The split version {version} must contains 4 parts')
        return int(parts[3])

    @staticmethod
    def is_valid_sonar_version(version: str) -> bool:
        if "." not in version:
            return False
        parts = version.split('.')
        if len(parts) != 4:
            return False

        return True

    @staticmethod
    def is_valid_plus_signed_version(version: str) -> bool:

        # This is an explicit requirement for project SLVSCODE
        # see https://sonarsource.atlassian.net/browse/BUILD-4915 for more details

        if not re.match(VersionHelper.VERSION_NUMBER_PLUS_SIGN_REGEX, version):
            return False

        return VersionHelper.is_valid_sonar_version(VersionHelper._sanitize_version(version))

    @staticmethod
    def is_valid_version(version: str) -> bool:
        return VersionHelper.is_valid_sonar_version(version) or VersionHelper.is_valid_plus_signed_version(version)

    @staticmethod
    def _sanitize_version(version: str) -> str:
        return version.replace("+", ".")
