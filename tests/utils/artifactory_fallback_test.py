"""
Tests for Artifactory fallback artifact functionality.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock

# Adjust path for local imports
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from utils.artifactory import Artifactory, ArtifactoryError
from utils.buildinfo import BuildInfo


class TestArtifactoryFallback(unittest.TestCase):
    """Test cases for Artifactory fallback artifact functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.artifactory = Artifactory("test-token")
        self.context = Mock()
        self.context.repository = "test-repo"
        self.context.version = "1.0.0.12345"
        self.context.branch = "master"

    @patch('utils.artifactory.Artifactory._download_single_artifact')
    @patch('utils.artifactory.Artifactory.get_build_info')
    def test_download_artifacts_with_fallback_success(self, mock_get_build_info, mock_download):
        """Test successful download with fallback artifact."""
        # Mock build info with no artifacts to publish but suitable fallback
        mock_build_info = Mock(spec=BuildInfo)
        mock_build_info.get_artifacts_to_publish.return_value = None
        mock_build_info.get_first_suitable_artifact.return_value = "org.sonarsource:plugin:1.0.0:jar"
        mock_get_build_info.return_value = mock_build_info

        # Mock successful download
        mock_download.return_value = {
            'path': '/tmp/plugin-1.0.0.jar',
            'name': 'plugin-1.0.0.jar'
        }

        result = self.artifactory.download_artifacts_from_build_info(self.context)

        # Verify the result
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'plugin-1.0.0.jar')

        # Verify fallback was called
        mock_build_info.get_first_suitable_artifact.assert_called_once()
        mock_download.assert_called_once()

    @patch('utils.artifactory.Artifactory.get_build_info')
    def test_download_artifacts_with_fallback_no_suitable_artifact(self, mock_get_build_info):
        """Test download when no suitable fallback artifact is found."""
        # Mock build info with no artifacts to publish and no suitable fallback
        mock_build_info = Mock(spec=BuildInfo)
        mock_build_info.get_artifacts_to_publish.return_value = None
        mock_build_info.get_first_suitable_artifact.return_value = None
        mock_get_build_info.return_value = mock_build_info

        result = self.artifactory.download_artifacts_from_build_info(self.context)

        # Should return empty list
        self.assertEqual(result, [])

    @patch('utils.artifactory.Artifactory._download_single_artifact')
    @patch('utils.artifactory.Artifactory.get_build_info')
    def test_download_artifacts_with_normal_artifacts(self, mock_get_build_info, mock_download):
        """Test download with normal artifacts to publish (no fallback needed)."""
        # Mock build info with normal artifacts to publish
        mock_build_info = Mock(spec=BuildInfo)
        mock_build_info.get_artifacts_to_publish.return_value = "org.sonarsource:plugin:1.0.0:jar"
        mock_get_build_info.return_value = mock_build_info

        # Mock successful download
        mock_download.return_value = {
            'path': '/tmp/plugin-1.0.0.jar',
            'name': 'plugin-1.0.0.jar'
        }

        result = self.artifactory.download_artifacts_from_build_info(self.context)

        # Verify the result
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'plugin-1.0.0.jar')

        # Verify fallback was NOT called
        mock_build_info.get_first_suitable_artifact.assert_not_called()
        mock_download.assert_called_once()

    @patch('utils.artifactory.Artifactory._download_single_artifact')
    @patch('utils.artifactory.Artifactory.get_build_info')
    def test_download_artifacts_with_fallback_private_project(self, mock_get_build_info, mock_download):
        """Test fallback with private project (com.sonarsource)."""
        # Mock build info for private project
        mock_build_info = Mock(spec=BuildInfo)
        mock_build_info.get_artifacts_to_publish.return_value = None
        mock_build_info.get_first_suitable_artifact.return_value = "com.sonarsource:private-plugin:2.0.0:jar"
        mock_get_build_info.return_value = mock_build_info

        # Mock successful download
        mock_download.return_value = {
            'path': '/tmp/private-plugin-2.0.0.jar',
            'name': 'private-plugin-2.0.0.jar'
        }

        result = self.artifactory.download_artifacts_from_build_info(self.context)

        # Verify the result
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'private-plugin-2.0.0.jar')

        # Verify fallback was called
        mock_build_info.get_first_suitable_artifact.assert_called_once()

    @patch('utils.artifactory.Artifactory.get_build_info')
    def test_download_artifacts_fallback_exception_handling(self, mock_get_build_info):
        """Test exception handling in fallback logic."""
        # Mock build info that raises exception in fallback
        mock_build_info = Mock(spec=BuildInfo)
        mock_build_info.get_artifacts_to_publish.return_value = None
        mock_build_info.get_first_suitable_artifact.side_effect = Exception("Fallback error")
        mock_get_build_info.return_value = mock_build_info

        with self.assertRaises(ArtifactoryError) as context:
            self.artifactory.download_artifacts_from_build_info(self.context)

        self.assertIn("Failed to download artifacts", str(context.exception))

    @patch('utils.artifactory.Artifactory._download_single_artifact')
    @patch('utils.artifactory.Artifactory.get_build_info')
    def test_download_artifacts_with_fallback_multiple_artifacts(self, mock_get_build_info, mock_download):
        """Test download with fallback returning multiple artifacts."""
        # Mock build info with fallback returning multiple artifacts
        mock_build_info = Mock(spec=BuildInfo)
        mock_build_info.get_artifacts_to_publish.return_value = None
        mock_build_info.get_first_suitable_artifact.return_value = "org.sonarsource:plugin1:1.0.0:jar,org.sonarsource:plugin2:2.0.0:jar"
        mock_get_build_info.return_value = mock_build_info

        # Mock successful downloads
        mock_download.side_effect = [
            {'path': '/tmp/plugin1-1.0.0.jar', 'name': 'plugin1-1.0.0.jar'},
            {'path': '/tmp/plugin2-2.0.0.jar', 'name': 'plugin2-2.0.0.jar'}
        ]

        result = self.artifactory.download_artifacts_from_build_info(self.context)

        # Verify the result
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['name'], 'plugin1-1.0.0.jar')
        self.assertEqual(result[1]['name'], 'plugin2-2.0.0.jar')

        # Verify fallback was called
        mock_build_info.get_first_suitable_artifact.assert_called_once()
        self.assertEqual(mock_download.call_count, 2)

    @patch('utils.artifactory.Artifactory._download_single_artifact')
    @patch('utils.artifactory.Artifactory.get_build_info')
    def test_download_artifacts_with_fallback_empty_string(self, mock_get_build_info, mock_download):
        """Test download with fallback returning empty string."""
        # Mock build info with empty artifacts to publish
        mock_build_info = Mock(spec=BuildInfo)
        mock_build_info.get_artifacts_to_publish.return_value = ""
        mock_build_info.get_first_suitable_artifact.return_value = "org.sonarsource:plugin:1.0.0:jar"
        mock_get_build_info.return_value = mock_build_info

        # Mock successful download
        mock_download.return_value = {
            'path': '/tmp/plugin-1.0.0.jar',
            'name': 'plugin-1.0.0.jar'
        }

        result = self.artifactory.download_artifacts_from_build_info(self.context)

        # Verify the result
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'plugin-1.0.0.jar')

        # Verify fallback was called
        mock_build_info.get_first_suitable_artifact.assert_called_once()

    @patch('utils.artifactory.Artifactory._download_single_artifact')
    @patch('utils.artifactory.Artifactory.get_build_info')
    def test_download_artifacts_with_fallback_whitespace_string(self, mock_get_build_info, mock_download):
        """Test download with fallback returning whitespace-only string."""
        # Mock build info with whitespace-only artifacts to publish
        mock_build_info = Mock(spec=BuildInfo)
        mock_build_info.get_artifacts_to_publish.return_value = "   "
        mock_build_info.get_first_suitable_artifact.return_value = "org.sonarsource:plugin:1.0.0:jar"
        mock_get_build_info.return_value = mock_build_info

        # Mock successful download
        mock_download.return_value = {
            'path': '/tmp/plugin-1.0.0.jar',
            'name': 'plugin-1.0.0.jar'
        }

        result = self.artifactory.download_artifacts_from_build_info(self.context)

        # Verify the result
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'plugin-1.0.0.jar')

        # Verify fallback was called
        mock_build_info.get_first_suitable_artifact.assert_called_once()


if __name__ == '__main__':
    unittest.main()
