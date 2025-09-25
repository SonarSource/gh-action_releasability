import os
import logging
from pathlib import Path
from typing import Optional

from ..inline_check import InlineCheck, CheckContext
from ..releasability_check_result import ReleasabilityCheckResult
from utils.artifactory import Artifactory
from utils.sonarqube import SonarQube

logger = logging.getLogger(__name__)


class CheckLicenses(InlineCheck):
    """Check for license compliance in the repository."""

    def __init__(self):
        """Initialize the CheckLicenses check."""
        # Get Artifactory token from environment
        self.artifactory_token = os.getenv("ARTIFACTORY_TOKEN")

        # Initialize Artifactory client if token is available
        if self.artifactory_token:
            self.artifactory = Artifactory(self.artifactory_token)
            logger.info("Artifactory client initialized")
        else:
            self.artifactory = None
            logger.warning("ARTIFACTORY_TOKEN not configured, artifact download will fail")

        # Get SonarQube token from environment
        self.sonarqube_token = os.getenv("SONARQUBE_TOKEN")

        # Initialize SonarQube client if token is available
        if self.sonarqube_token:
            self.sonarqube = SonarQube("https://next.sonarqube.com", self.sonarqube_token)
            logger.info("SonarQube client initialized")
        else:
            self.sonarqube = None
            logger.warning("SONARQUBE_TOKEN not configured, SBOM download will fail")

    @property
    def name(self) -> str:
        return "CheckLicenses"

    def execute(self, context: CheckContext) -> ReleasabilityCheckResult:
        """
        Execute the license check by downloading and analyzing artifacts.

        Args:
            context: CheckContext containing repository information

        Returns:
            ReleasabilityCheckResult with check status and details
        """
        try:
            logger.info(f"Starting license check for {context.repository} version {context.version}")

            # Check if Artifactory is configured
            if not self.artifactory:
                return self._create_error_result("Artifactory not configured. Set ARTIFACTORY_TOKEN environment variable.")

            # Download artifacts from Artifactory
            artifacts = self._download_artifacts(context)
            if not artifacts:
                return self._create_failed_result("No artifacts found for download")

            # Log downloaded artifacts
            self._log_artifacts(artifacts)

            # Download SBOM from SonarQube
            sbom_data = self._download_sbom(context)

            # Prepare and return success result
            message = self._build_success_message(context, artifacts, sbom_data)
            return ReleasabilityCheckResult(
                name=self.name,
                state=ReleasabilityCheckResult.CHECK_PASSED,
                message=message
            )

        except Exception as e:
            logger.error(f"License check failed with error: {e}")
            return self._create_error_result(f"License check error: {str(e)}")

    def _download_artifacts(self, context: CheckContext) -> list:
        """Download artifacts from Artifactory."""
        logger.info("Downloading artifacts from Artifactory...")
        return self.artifactory.download_artifacts_from_build_info(context)

    def _log_artifacts(self, artifacts: list) -> None:
        """Log information about downloaded artifacts."""
        logger.info(f"Successfully downloaded {len(artifacts)} artifacts:")
        for artifact in artifacts:
            file_size = Path(artifact['path']).stat().st_size if Path(artifact['path']).exists() else 0
            logger.info(f"  - {artifact['name']} ({file_size:,} bytes)")

    def _download_sbom(self, context: CheckContext) -> Optional[dict]:
        """Download SBOM from SonarQube if configured."""
        if not self.sonarqube:
            logger.warning("SonarQube not configured, skipping SBOM download")
            return None

        logger.info("Downloading SBOM from SonarQube...")
        try:
            component = self.sonarqube.get_project_key_from_env()
            if not component:
                logger.warning("SONAR_PROJECT_KEY environment variable not set, skipping SBOM download")
                return None

            sbom_data = self.sonarqube.download_sbom(component, context.branch)
            if sbom_data:
                components_count = len(sbom_data.get('components', []))
                logger.info(f"Successfully downloaded SBOM with {components_count} components")
            else:
                logger.warning("Failed to download SBOM from SonarQube")
            return sbom_data

        except Exception as e:
            logger.error(f"Error downloading SBOM: {e}")
            return None

    def _build_success_message(self, context: CheckContext, artifacts: list, sbom_data: dict) -> str:
        """Build success message with artifact and SBOM information."""
        artifact_names = [artifact['name'] for artifact in artifacts]
        message_parts = [f"downloaded {len(artifacts)} artifacts: {', '.join(artifact_names)}"]

        if sbom_data:
            components_count = len(sbom_data.get('components', []))
            message_parts.append(f"downloaded SBOM with {components_count} components")

        return f"License check for {context.repository} - " + ", ".join(message_parts)

    def _create_error_result(self, message: str) -> ReleasabilityCheckResult:
        """Create an error result with the given message."""
        return ReleasabilityCheckResult(
            name=self.name,
            state=ReleasabilityCheckResult.CHECK_ERROR,
            message=message
        )

    def _create_failed_result(self, message: str) -> ReleasabilityCheckResult:
        """Create a failed result with the given message."""
        return ReleasabilityCheckResult(
            name=self.name,
            state=ReleasabilityCheckResult.CHECK_FAILED,
            message=message
        )
