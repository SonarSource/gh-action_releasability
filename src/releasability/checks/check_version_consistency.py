import re
from typing import Optional

from utils.artifactory_client import ArtifactoryClient
from utils.version_helper import VersionHelper

from ..inline_check import CheckContext, InlineCheck
from ..releasability_check_result import ReleasabilityCheckResult


class CheckVersionConsistency(InlineCheck):
    """
    Ensure the releasability input Major.Minor.Patch matches the Repox build-info
    module version (same source used later by gh-action_release for CDN naming).
    """

    def __init__(self, artifactory_client: Optional[ArtifactoryClient] = None):
        self._artifactory_client = artifactory_client

    @property
    def name(self) -> str:
        return "CheckVersionConsistency"

    def execute(self, context: CheckContext) -> ReleasabilityCheckResult:
        client = self._artifactory_client or ArtifactoryClient.from_env()

        build_name = VersionHelper.artifactory_build_name(context.repository, context.version)
        build_number = VersionHelper.extract_build_number(context.version)
        input_mmp = VersionHelper.extract_major_minor_patch(context.version)

        build_info = client.fetch_build_info(build_name, build_number)
        modules = build_info.get('modules') or []
        if not modules:
            return ReleasabilityCheckResult(
                self.name,
                ReleasabilityCheckResult.CHECK_ERROR,
                f'build-info for {build_name}:{build_number} has no modules',
            )

        module_id = modules[0].get('id')
        if not module_id:
            return ReleasabilityCheckResult(
                self.name,
                ReleasabilityCheckResult.CHECK_ERROR,
                f'first build-info module for {build_name}:{build_number} has no id',
            )

        artifact_version = VersionHelper.parse_module_version(module_id)
        artifact_mmp = VersionHelper.major_minor_patch_from_artifact_version(artifact_version)

        if input_mmp != artifact_mmp:
            return ReleasabilityCheckResult(
                self.name,
                ReleasabilityCheckResult.CHECK_FAILED,
                (
                    f'input version Major.Minor.Patch ({input_mmp}) does not match '
                    f'Repox build-info module version ({artifact_mmp})'
                ),
            )

        artifact_build = self._extract_trailing_build_number(artifact_version)
        if artifact_build is not None and artifact_build != build_number:
            return ReleasabilityCheckResult(
                self.name,
                ReleasabilityCheckResult.CHECK_FAILED,
                (
                    f'input build number ({build_number}) does not match '
                    f'Repox build-info module build number ({artifact_build})'
                ),
            )

        return ReleasabilityCheckResult(
            self.name,
            ReleasabilityCheckResult.CHECK_PASSED,
            f'input {input_mmp}.{build_number} matches Repox module {artifact_version}',
        )

    @staticmethod
    def _extract_trailing_build_number(artifact_version: str) -> Optional[int]:
        match = re.search(r'[.+-](\d+)$', artifact_version.strip())
        return int(match.group(1)) if match else None
