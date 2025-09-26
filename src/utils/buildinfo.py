import logging
from typing import Optional

logger = logging.getLogger(__name__)


class BuildInfo:

    def __init__(self, json):
        self.json = json

    def get_property(self, property_name, default=None):
        try:
            return self.json['buildInfo']['properties'][property_name]
        except KeyError:
            return default

    def get_module_property(self, property_name, default=None):
        try:
            return self.json['buildInfo']['modules'][0]['properties'][property_name]
        except (KeyError, IndexError):
            return default

    def get_version(self):
        try:
            return self.json['buildInfo']['modules'][0]['id'].split(":")[-1]
        except (KeyError, IndexError):
            return None

    def get_artifacts_to_publish(self):
        artifacts = self.get_module_property('artifactsToPublish', self.get_property('buildInfo.env.ARTIFACTS_TO_PUBLISH'))
        if not artifacts:
            logger.info("No artifacts to publish")
        return artifacts

    def is_public(self):
        artifacts = self.get_artifacts_to_publish()
        if artifacts:
            return "org.sonarsource" in artifacts
        else:
            return False

    def get_package(self):
        allartifacts = self.get_artifacts_to_publish()
        if not allartifacts:
            return None
        artifacts = allartifacts.split(",")
        artifacts_count = len(artifacts)
        if artifacts_count > 0:
            artifact = artifacts[0].strip()
            if not artifact:  # Empty string after stripping
                return None
            parts = artifact.split(":")
            if len(parts) >= 2:  # Must have at least groupId:artifactId
                return parts[0].strip()
        return None

    def get_first_suitable_artifact(self, is_public: bool = None) -> Optional[str]:
        """
        Get the first suitable artifact from build info when artifactsToPublish is empty.

        Args:
            is_public: Whether this is a public project. If None, will be determined from existing artifacts.

        Returns:
            Artifact string in format "groupId:artifactId:version:type:filename:original_repo" or None if not found
        """
        try:
            is_public = is_public if is_public is not None else self.is_public()
            modules = self.json.get('buildInfo', {}).get('modules', [])

            for module in modules:
                artifact_string = self._find_suitable_artifact_in_module(module, is_public)
                if artifact_string:
                    return artifact_string

            logger.warning("No suitable artifacts found in build info")
            return None

        except Exception as e:
            logger.error(f"Error finding suitable artifact: {e}")
            return None

    def _find_suitable_artifact_in_module(self, module: dict, is_public: bool) -> Optional[str]:
        """Find the first suitable artifact in a module."""
        artifacts = module.get('artifacts', [])
        for artifact in artifacts:
            if self._is_suitable_artifact(artifact):
                return self._build_artifact_string(artifact, module, is_public)
        return None

    def _build_artifact_string(self, artifact: dict, module: dict, is_public: bool) -> str:
        """Build artifact string from artifact and module information."""
        artifact_name = artifact.get('name', '')
        artifact_type = artifact.get('type', 'jar')

        group_id, artifact_id, version = self._extract_coordinates_from_module(module, artifact_name, artifact_type, is_public)
        original_repo = artifact.get('originalDeploymentRepo', '')

        if original_repo:
            return f"{group_id}:{artifact_id}:{version}:{artifact_type}:{artifact_name}:{original_repo}"
        else:
            return f"{group_id}:{artifact_id}:{version}:{artifact_type}:{artifact_name}"

    def _extract_coordinates_from_module(self, module: dict, artifact_name: str, artifact_type: str, is_public: bool) -> tuple[str, str, str]:
        """Extract group_id, artifact_id, and version from module information."""
        module_id = module.get('id', '')

        if ':' in module_id and self._is_valid_module_id(module_id):
            return self._parse_module_id(module_id)
        else:
            return self._create_fallback_coordinates(artifact_name, artifact_type, is_public)

    def _is_valid_module_id(self, module_id: str) -> bool:
        """Check if module ID has valid format."""
        parts = module_id.split(':')
        return len(parts) >= 3

    def _parse_module_id(self, module_id: str) -> tuple[str, str, str]:
        """Parse module ID to extract coordinates."""
        parts = module_id.split(':')
        return parts[0], parts[1], parts[2]

    def _create_fallback_coordinates(self, artifact_name: str, artifact_type: str, is_public: bool) -> tuple[str, str, str]:
        """Create fallback coordinates when module ID is invalid."""
        group_id = 'org.sonarsource' if is_public else 'com.sonarsource'
        artifact_id = self._extract_artifact_id_from_name(artifact_name, artifact_type)
        version = self.get_version() or '1.0.0'
        return group_id, artifact_id, version

    def _extract_artifact_id_from_name(self, artifact_name: str, artifact_type: str) -> str:
        """Extract artifact ID from artifact name."""
        if artifact_name.endswith(f'.{artifact_type}'):
            return artifact_name.replace(f'.{artifact_type}', '')
        return artifact_name

    def _is_suitable_artifact(self, artifact: dict) -> bool:
        """
        Check if an artifact is suitable for download.

        Args:
            artifact: Artifact dictionary from build info

        Returns:
            True if artifact is suitable, False otherwise
        """
        try:
            # Check if it's a supported file type (JAR or NUPKG)
            artifact_type = artifact.get('type', '').lower()
            if artifact_type not in ['jar', 'nupkg']:
                return False

            # Check that it's not sources or javadoc
            artifact_name = artifact.get('name', '').lower()
            if 'sources' in artifact_name or 'javadoc' in artifact_name:
                return False

            return True

        except Exception as e:
            logger.debug(f"Error checking artifact suitability: {e}")
            return False
