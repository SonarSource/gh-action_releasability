"""
Simple integration test for artifact download functionality.
"""

import unittest
import os
from unittest.mock import patch, MagicMock

# Add src to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from releasability.inline_check import CheckContext
from utils.artifactory import Artifactory


class TestArtifactDownload(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures."""
        self.context = CheckContext(
            organization="sonar",
            repository="SonarJS",
            branch="master",
            version="11.4.0.34681",
            commit_sha="b46688449f8d3d5f5b4052abe50c74bba0e0220a"
        )
        self.artifactory = Artifactory("test-token")

    @patch('utils.artifactory.ArtifactoryPath')
    def test_get_build_info_with_context(self, mock_artifactory_path):
        """Test that get_build_info works with CheckContext."""
        # Mock the ArtifactoryPath and its open method
        mock_path_instance = MagicMock()
        mock_artifactory_path.return_value = mock_path_instance

        # Mock the file-like object returned by open()
        mock_file = MagicMock()
        mock_file.read.return_value = '{"buildInfo": {"modules": [{"id": "org.sonarsource.javascript:javascript:11.4.0.34681"}]}}'
        mock_path_instance.open.return_value.__enter__.return_value = mock_file

        result = self.artifactory.get_build_info(self.context.repository, "34681")

        # Verify the result
        self.assertIsNotNone(result)
        self.assertEqual(result.json['buildInfo']['modules'][0]['id'], 'org.sonarsource.javascript:javascript:11.4.0.34681')

    @patch('utils.artifactory.Artifactory.get_build_info')
    @patch('utils.artifactory.Artifactory._download_single_artifact')
    def test_download_artifacts_integration(self, mock_download, mock_get_build_info):
        """Test full integration of artifact download."""
        # Mock build info
        mock_build_info = MagicMock()
        mock_build_info.get_artifacts_to_publish.return_value = "org.sonarsource:plugin:jar"
        mock_get_build_info.return_value = mock_build_info

        # Mock download
        mock_download.return_value = {
            'path': '/tmp/plugin-11.4.0.34681.jar',
            'name': 'plugin-11.4.0.34681.jar',
            'group_id': 'org.sonarsource',
            'artifact_id': 'plugin',
            'version': '11.4.0.34681',
            'extension': 'jar',
            'classifier': None
        }

        result = self.artifactory.download_artifacts_from_build_info(self.context)

        # Verify the result
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'plugin-11.4.0.34681.jar')
        self.assertEqual(result[0]['group_id'], 'org.sonarsource')
        self.assertEqual(result[0]['artifact_id'], 'plugin')


if __name__ == '__main__':
    unittest.main()
