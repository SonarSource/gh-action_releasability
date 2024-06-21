import re


class VersionHelper:
    VERSION_REGEX = (
        r'^'                  # Start of the string
        r'(?:[a-zA-Z]+-)?'    # Optional ProjectName- prefix in a non-capturing group (see https://sonarsource.atlassian.net/browse/BUILD-5293)
        r'\d+\.\d+\.\d+'      # Major.Minor.Patch version
        r'(?:-M\d+)?'         # Optional -Mx suffix in a non-capturing group
        r'[.+]'               # Separator, either . or + (see https://sonarsource.atlassian.net/browse/BUILD-4915)
        r'(\d+)$'             # Build number in a captured group
    )

    @staticmethod
    def validate_version(version: str) -> None:
        """
        Validates the version string against the expected format.

        Parameters:
        - version (str): The version string to validate.

        Raises:
        - ValueError: If the version does not match the expected format.
        """
        if not re.match(VersionHelper.VERSION_REGEX, version):
            raise ValueError(
                'The tag must follow this pattern: [ProjectName-]Major.Minor.Patch[-Mx][.+]BuildNumber\n'
                'Where:\n'
                '- "ProjectName-" is an optional prefix (any sequence of letters followed by a dash).\n'
                '- "Major.Minor.Patch" is the version number (three numbers separated by dots).\n'
                '- "-Mx" is an optional suffix (a dash followed by "M" and a number).\n'
                '- "[.+]" is a separator, either a dot or a plus sign.\n'
                '- "BuildNumber" is the build number (a number at the end of the string).'
            )

    @staticmethod
    def extract_build_number(version: str) -> int:
        """
        Extracts the build number from a validated version string.

        Parameters:
        - version (str): The version string from which to extract the build number.

        Returns:
        - int: The extracted build number.
        """
        VersionHelper.validate_version(version)
        match = re.match(VersionHelper.VERSION_REGEX, version)
        # Extract the build number (the first capturing group in the regex)
        build_number = match.group(1)
        return int(build_number)
