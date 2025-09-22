import logging

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

    def get_source_and_target_repos(self, revoke):
        try:
            repo = self.json['buildInfo']['statuses'][0]['repository']
            repo_type = repo.split('-')[-1]
            if revoke:
                sourcerepo = repo.replace(repo_type, 'releases')
                targetrepo = repo.replace(repo_type, 'builds')
            else:
                sourcerepo = repo.replace(repo_type, 'builds')
                targetrepo = repo.replace(repo_type, 'releases')
            return sourcerepo, targetrepo
        except (KeyError, IndexError):
            return None, None

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
