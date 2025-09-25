"""
Simple tests for Artifactory client using dohq-artifactory library.
"""

import unittest
import os
import tempfile
from unittest.mock import patch, MagicMock

# Adjust path for local imports
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from utils.artifactory import Artifactory, ArtifactoryError
from utils.buildinfo import BuildInfo
from releasability.inline_check import CheckContext


class TestArtifactory(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures."""
        self.artifactory = Artifactory("test-token")
        self.context = CheckContext(
            organization="sonar",
            repository="SonarJS",
            branch="master",
            version="11.4.0.34681",
            commit_sha="b46688449f8d3d5f5b4052abe50c74bba0e0220a"
        )

    def test_init(self):
        """Test Artifactory initialization."""
        self.assertEqual(self.artifactory.access_token, "test-token")
        self.assertEqual(self.artifactory.base_url, "https://repox.jfrog.io/repox")
        self.assertEqual(self.artifactory.auth, ("", "test-token"))

    @patch('utils.artifactory.ArtifactoryPath')
    def test_get_build_info_success(self, mock_artifactory_path):
        """Test successful build info retrieval."""
        # Mock the ArtifactoryPath and its open method
        mock_path_instance = MagicMock()
        mock_artifactory_path.return_value = mock_path_instance

        # Mock the file-like object returned by open()
        mock_file = MagicMock()
        mock_file.read.return_value = '{"buildInfo": {"modules": [{"id": "org.sonarsource.javascript:javascript:11.4.0.34681"}]}}'
        mock_path_instance.open.return_value.__enter__.return_value = mock_file

        result = self.artifactory.get_build_info("SonarJS", "34681")

        # Verify the ArtifactoryPath was created correctly
        expected_url = "https://repox.jfrog.io/repox/api/build/SonarJS/34681"
        mock_artifactory_path.assert_called_once_with(expected_url, auth=self.artifactory.auth)

        # Verify the result
        self.assertIsInstance(result, BuildInfo)
        self.assertEqual(result.json['buildInfo']['modules'][0]['id'], 'org.sonarsource.javascript:javascript:11.4.0.34681')

    @patch('utils.artifactory.ArtifactoryPath')
    def test_get_build_info_error(self, mock_artifactory_path):
        """Test build info retrieval with error."""
        # Mock the ArtifactoryPath to raise an exception
        mock_path_instance = MagicMock()
        mock_artifactory_path.return_value = mock_path_instance
        mock_path_instance.open.side_effect = Exception("Network error")

        with self.assertRaises(ArtifactoryError) as context:
            self.artifactory.get_build_info("SonarJS", "34681")

        self.assertIn("Failed to get build info: Network error", str(context.exception))

    def test_parse_artifact_string_full_format(self):
        """Test parsing artifact string with full format."""
        artifact_str = "org.sonarsource:plugin:1.0.0:jar:sources"
        result = self.artifactory._parse_artifact_string(artifact_str, self.context)

        expected = {
            'group_id': 'org.sonarsource',
            'artifact_id': 'plugin',
            'version': '1.0.0',
            'extension': 'jar',
            'classifier': 'sources'
        }
        self.assertEqual(result, expected)

    def test_parse_artifact_string_short_format(self):
        """Test parsing artifact string with short format."""
        artifact_str = "org.sonarsource:plugin:jar"
        result = self.artifactory._parse_artifact_string(artifact_str, self.context)

        expected = {
            'group_id': 'org.sonarsource',
            'artifact_id': 'plugin',
            'version': '11.4.0.34681',  # From context
            'extension': 'jar',
            'classifier': None
        }
        self.assertEqual(result, expected)

    def test_parse_artifact_string_invalid(self):
        """Test parsing invalid artifact string."""
        artifact_str = "invalid"
        result = self.artifactory._parse_artifact_string(artifact_str, self.context)
        self.assertIsNone(result)

    @patch('utils.artifactory.ArtifactoryPath')
    def test_download_single_artifact_success(self, mock_artifactory_path):
        """Test successful single artifact download."""
        # Mock the ArtifactoryPath and its open method
        mock_path_instance = MagicMock()
        mock_artifactory_path.return_value = mock_path_instance

        # Mock the file-like object returned by open()
        mock_path_instance.read_bytes.return_value = b"fake jar content"
        artifact_info = {
            'group_id': 'org.sonarsource',
            'artifact_id': 'plugin',
            'version': '1.0.0',
            'extension': 'jar',
            'classifier': None
        }

        result = self.artifactory._download_single_artifact(artifact_info)

        # Verify the result
        self.assertIsNotNone(result)
        self.assertEqual(result['group_id'], 'org.sonarsource')
        self.assertEqual(result['artifact_id'], 'plugin')
        self.assertEqual(result['version'], '1.0.0')
        self.assertEqual(result['extension'], 'jar')
        self.assertIsNone(result['classifier'])
        self.assertEqual(result['name'], 'plugin-1.0.0.jar')
        self.assertTrue(result['path'].endswith('plugin-1.0.0.jar'))

    @patch('utils.artifactory.ArtifactoryPath')
    def test_download_single_artifact_error(self, mock_artifactory_path):
        """Test single artifact download with error."""
        # Mock the ArtifactoryPath to raise an exception
        mock_path_instance = MagicMock()
        mock_artifactory_path.return_value = mock_path_instance
        mock_path_instance.open.side_effect = Exception("Download failed")

        artifact_info = {
            'group_id': 'org.sonarsource',
            'artifact_id': 'plugin',
            'version': '1.0.0',
            'extension': 'jar',
            'classifier': None
        }

        result = self.artifactory._download_single_artifact(artifact_info)
        self.assertIsNone(result)

    @patch('utils.artifactory.Artifactory.get_build_info')
    @patch('utils.artifactory.Artifactory._download_single_artifact')
    def test_download_artifacts_from_build_info_success(self, mock_download, mock_get_build_info):
        """Test successful download of artifacts from build info."""
        # Mock build info
        mock_build_info = MagicMock()
        mock_build_info.get_artifacts_to_publish.return_value = "org.sonarsource:plugin:jar,com.sonarsource:plugin2:zip"
        mock_get_build_info.return_value = mock_build_info

        # Mock downloads
        mock_download.side_effect = [
            {'path': '/tmp/plugin-11.4.0.34681.jar', 'name': 'plugin-11.4.0.34681.jar'},
            {'path': '/tmp/plugin2-11.4.0.34681.zip', 'name': 'plugin2-11.4.0.34681.zip'}
        ]

        result = self.artifactory.download_artifacts_from_build_info(self.context)

        # Verify the result
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['name'], 'plugin-11.4.0.34681.jar')
        self.assertEqual(result[1]['name'], 'plugin2-11.4.0.34681.zip')

    @patch('utils.artifactory.Artifactory.get_build_info')
    def test_download_artifacts_from_build_info_no_artifacts(self, mock_get_build_info):
        """Test download when no artifacts to publish."""
        # Mock build info with no artifacts
        mock_build_info = MagicMock()
        mock_build_info.get_artifacts_to_publish.return_value = ""
        mock_get_build_info.return_value = mock_build_info

        result = self.artifactory.download_artifacts_from_build_info(self.context)

        # Verify the result
        self.assertEqual(result, [])

    @patch('utils.artifactory.Artifactory.get_build_info')
    def test_download_artifacts_from_build_info_error(self, mock_get_build_info):
        """Test download artifacts with error."""
        # Mock build info to raise an exception
        mock_get_build_info.side_effect = Exception("Build info error")

        with self.assertRaises(ArtifactoryError) as context:
            self.artifactory.download_artifacts_from_build_info(self.context)

        self.assertIn("Failed to download artifacts: Build info error", str(context.exception))


if __name__ == '__main__':
    unittest.main()
