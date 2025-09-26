"""
Simple Artifactory client using dohq-artifactory library.
"""

import json
import logging
import tempfile
from pathlib import Path
from typing import List, Dict, Optional

from artifactory import ArtifactoryPath
from dryable import Dryable

from .buildinfo import BuildInfo

logger = logging.getLogger(__name__)


class ArtifactoryError(Exception):
    """Exception raised for Artifactory-related errors."""
    pass


class Artifactory:
    """Simple Artifactory client using dohq-artifactory library."""

    def __init__(self, access_token: str, base_url: str = "https://repox.jfrog.io/repox"):
        """Initialize the Artifactory client."""
        self.access_token = access_token
        self.base_url = base_url
        self.auth = ("", access_token)  # dohq-artifactory uses (username, token) format

    @Dryable(logging_msg='{function}()')
    def get_build_info(self, project: str, build_number: str) -> BuildInfo:
        """Get build info from Artifactory."""
        try:
            url = f"{self.base_url}/api/build/{project}/{build_number}"
            logger.info(f"Fetching build info from: {url}")

            build_path = ArtifactoryPath(url, auth=self.auth)
            with build_path.open('r') as f:
                build_data = f.read()

            buildinfo = json.loads(build_data)
            logger.info(f"Successfully retrieved build info for {project} build {build_number}")
            return BuildInfo(buildinfo)

        except Exception as e:
            logger.error(f"Failed to get build info: {e}")
            raise ArtifactoryError(f"Failed to get build info: {e}")

    def download_artifacts_from_build_info(self, context) -> List[Dict]:
        """Download all artifacts specified in the build info artifactsToPublish."""
        try:
            # Extract build number from version
            build_number = context.version.split('.')[-1] if '.' in context.version else context.version

            # Get build info
            build_info = self.get_build_info(context.repository, build_number)
            artifacts_to_publish = build_info.get_artifacts_to_publish()

            if not artifacts_to_publish or not artifacts_to_publish.strip():
                logger.warning("No artifacts to publish found in build info, trying to find suitable artifact...")

                # Try to find the first suitable artifact as fallback
                fallback_artifact = build_info.get_first_suitable_artifact()
                if fallback_artifact:
                    logger.info(f"Found suitable fallback artifact: {fallback_artifact}")
                    artifacts_to_publish = fallback_artifact
                else:
                    logger.warning("No suitable artifacts found in build info")
                    return []

            # Download each artifact
            downloaded_artifacts = []
            for artifact_str in artifacts_to_publish.split(','):
                artifact_str = artifact_str.strip()
                if not artifact_str:
                    continue

                artifact_info = self._parse_artifact_string(artifact_str, context)
                if artifact_info:
                    downloaded_artifact = self._download_single_artifact(artifact_info)
                    if downloaded_artifact:
                        downloaded_artifacts.append(downloaded_artifact)

            logger.info(f"Successfully downloaded {len(downloaded_artifacts)} artifacts")
            return downloaded_artifacts

        except Exception as e:
            logger.error(f"Failed to download artifacts: {e}")
            raise ArtifactoryError(f"Failed to download artifacts: {e}")

    def _parse_artifact_string(self, artifact_str: str, context) -> Optional[Dict]:
        """Parse artifact string and return artifact information."""
        logger.info(f"Parsing artifact string: {artifact_str}")
        parts = artifact_str.split(':')
        logger.info(f"Split into {len(parts)} parts: {parts}")
        if len(parts) < 3:
            logger.warning(f"Artifact string has too few parts: {len(parts)}")
            return None

        group_id = parts[0]
        artifact_id = parts[1]

        # Initialize all variables
        actual_filename = None
        original_repo = None
        classifier = None

        if len(parts) >= 6:
            # Format: "groupId:artifactId:version:extension:actual_filename:original_repo" (fallback format)
            version = parts[2]
            extension = parts[3]
            actual_filename = parts[4]
            original_repo = parts[5]
        elif len(parts) >= 5:
            # Check if this is a fallback format (has actual_filename) or normal format (has classifier)
            # Fallback format: "groupId:artifactId:version:extension:actual_filename"
            # Normal format: "groupId:artifactId:version:extension:classifier"
            version = parts[2]
            extension = parts[3]
            # For now, assume it's a classifier unless we have more context
            # This will be handled by the calling code based on whether original_repo is available
            classifier = parts[4]
        elif len(parts) >= 4:
            # Format: "groupId:artifactId:version:extension:classifier"
            version = parts[2]
            extension = parts[3]
            classifier = parts[4] if len(parts) > 4 else None
        else:
            # Format: "groupId:artifactId:extension" - version from context
            version = context.version
            extension = parts[2]

        return {
            'group_id': group_id,
            'artifact_id': artifact_id,
            'version': version,
            'extension': extension,
            'classifier': classifier,
            'actual_filename': actual_filename,
            'original_repo': original_repo
        }

    def _download_single_artifact(self, artifact_info: Dict) -> Optional[Dict]:
        """Download a single artifact and return its information."""
        group_id = artifact_info['group_id']
        artifact_id = artifact_info['artifact_id']
        version = artifact_info['version']
        extension = artifact_info['extension']
        classifier = artifact_info['classifier']
        actual_filename = artifact_info.get('actual_filename')
        original_repo = artifact_info.get('original_repo')

        try:
            # Determine repository based on package type and group ID
            if extension.lower() in ['nupkg']:
                # NuGet packages use different repositories
                repository = "sonarsource-nuget-private-builds" if group_id.startswith('com.') else "sonarsource-nuget-public"
            else:
                # Regular packages (JAR, ZIP, etc.)
                repository = "sonarsource-private-builds" if group_id.startswith('com.') else "sonarsource-public-builds"

            # Build artifact path
            if actual_filename:
                # For fallback case with actual filename, use direct path
                # dohq-artifactory will prepend /api/storage/, so we need to adjust the base URL
                filename = actual_filename
                # Use the base URL without /repox/ since dohq-artifactory will add /api/storage/
                if self.base_url.endswith('/repox'):
                    base_url_without_repox = self.base_url[:-6]  # Remove '/repox' from the end
                else:
                    base_url_without_repox = self.base_url
                artifact_url = f"{base_url_without_repox}/artifactory/{repository}/{filename}"
                logger.info(f"Fallback artifact URL: {artifact_url}")
            else:
                # Normal case - use Maven-style path structure
                group_path = group_id.replace(".", "/")

                if actual_filename:
                    # Use the actual filename from build info (fallback case)
                    filename = actual_filename
                else:
                    # Construct filename from components (normal case)
                    filename = f"{artifact_id}-{version}"
                    if classifier:
                        filename += f"-{classifier}"
                    filename += f".{extension}"

                # Special case for sonarqube
                if artifact_id == "sonar-application":
                    filename = f"sonarqube-{version}.zip"

                # Use the base URL without /repox/ since dohq-artifactory will add /api/storage/
                if self.base_url.endswith('/repox'):
                    base_url_without_repox = self.base_url[:-6]  # Remove '/repox' from the end
                else:
                    base_url_without_repox = self.base_url
                artifact_url = f"{base_url_without_repox}/artifactory/{repository}/{group_path}/{artifact_id}/{version}/{filename}"
            artifact_path = ArtifactoryPath(artifact_url, auth=self.auth)

            # Download to temp file
            temp_file = Path(tempfile.gettempdir()) / filename
            with temp_file.open('wb') as dst:
                dst.write(artifact_path.read_bytes())

            logger.info(f"Downloaded artifact: {filename}")

            return {
                'path': str(temp_file),
                'size': temp_file.stat().st_size,
                'group_id': group_id,
                'artifact_id': artifact_id,
                'version': version,
                'extension': extension,
                'classifier': classifier,
                'name': filename
            }

        except Exception as e:
            logger.error(f"Failed to download artifact {artifact_id}-{version}: {e}")
            return None
