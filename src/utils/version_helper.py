import re


class VersionHelper:
    VERSION_REGEX = (
        r'^(?:[a-zA-Z]+-)?'   # Optional ProjectName- prefix (required by sonar-scanner-azdo; see https://sonarsource.atlassian.net/browse/BUILD-5293)
        r'\d+\.\d+\.\d+'      # Major.Minor.Patch version
        r'(?:-M\d+)?'         # Optional -Mx suffix
        r'[.+-]'              # Separator (+ is required by sonarlint-vscode; see https://sonarsource.atlassian.net/browse/BUILD-4915)
                              # Separator (- is required by npmjs projects; npm version command do not support x.x.x.xxxx format)
        r'(\d+)$'             # Build number in a captured group
    )

    # Groups: optional prefix, major.minor.patch[+optional -Mx], build number
    VERSION_PARSE_REGEX = re.compile(
        r'^(?:([a-zA-Z]+)-)?'
        r'(\d+\.\d+\.\d+(?:-M\d+)?)'
        r'[.+-]'
        r'(\d+)$'
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
        if not version or not isinstance(version, str):
            raise ValueError(
                f'Version must be a non-empty string. Received: {repr(version)}'
            )
        # Strip whitespace in case it was passed with leading/trailing spaces
        version_stripped = version.strip()
        if not re.match(VersionHelper.VERSION_REGEX, version_stripped):
            raise ValueError(
                'The tag must follow this pattern: [ProjectName-]Major.Minor.Patch[-Mx][.+-]BuildNumber\n'
                'Where:\n'
                '- "ProjectName-" is an optional prefix (any sequence of letters followed by a dash).\n'
                '- "Major.Minor.Patch" is the version number (three numbers separated by dots).\n'
                '- "-Mx" is an optional suffix (a dash followed by "M" and a number).\n'
                '- "[.+-]" is a separator, either a dot, a plus sign, or a minus sign.\n'
                '- "BuildNumber" is the build number (a number at the end of the string).\n'
                f'Received version: "{version}" (length: {len(version)})'
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

    @staticmethod
    def extract_project_prefix(version: str) -> str | None:
        """Return the optional alphabetic project prefix (e.g. 'sqs'), or None."""
        VersionHelper.validate_version(version)
        match = VersionHelper.VERSION_PARSE_REGEX.match(version.strip())
        return match.group(1) if match else None

    @staticmethod
    def extract_major_minor_patch(version: str) -> str:
        """
        Return Major.Minor.Patch from a releasability version string.

        Examples:
        - 'sqs-2026.4.0.125719' -> '2026.4.0'
        - '1.2.3+4567' -> '1.2.3'
        - '1.2.3-M1.4567' -> '1.2.3-M1'
        """
        VersionHelper.validate_version(version)
        match = VersionHelper.VERSION_PARSE_REGEX.match(version.strip())
        if not match:
            raise ValueError(f'Unable to parse Major.Minor.Patch from version: {version}')
        return match.group(2)

    @staticmethod
    def artifactory_build_name(repository: str, version: str) -> str:
        """
        Build name used to fetch Repox build-info (matches ops-releasability).

        Prefixed versions use '{repository}-{prefix}' (e.g. sonar-enterprise-sqs).
        """
        prefix = VersionHelper.extract_project_prefix(version)
        return f'{repository}-{prefix}' if prefix else repository

    @staticmethod
    def parse_module_version(module_id: str) -> str:
        """
        Extract the version coordinate from a Maven module id 'group:artifact:version'.
        """
        parts = module_id.split(':')
        if len(parts) < 3 or not parts[-1]:
            raise ValueError(f'Unable to parse version from module id: {module_id}')
        return parts[-1]

    @staticmethod
    def major_minor_patch_from_artifact_version(artifact_version: str) -> str:
        """
        Normalize a Repox module version to Major.Minor.Patch.

        Accepts dotted build versions and semver separators (+/-) before the build number.
        """
        match = re.match(
            r'^(\d+\.\d+\.\d+(?:-M\d+)?)(?:[.+-]\d+)?$',
            artifact_version.strip(),
        )
        if not match:
            # Fallback: take first three numeric components
            components = re.split(r'[.+-]', artifact_version.strip())
            numeric = [c for c in components if c.isdigit()]
            if len(numeric) < 3:
                raise ValueError(
                    f'Unable to parse Major.Minor.Patch from artifact version: {artifact_version}'
                )
            return f'{numeric[0]}.{numeric[1]}.{numeric[2]}'
        return match.group(1)
