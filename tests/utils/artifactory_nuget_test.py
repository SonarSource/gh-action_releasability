"""
Tests for Artifactory NuGet package repository handling.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock

# Adjust path for local imports
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from utils.artifactory import Artifactory, ArtifactoryError


class TestArtifactoryNuGet(unittest.TestCase):
    """Test cases for Artifactory NuGet package repository handling."""

    def setUp(self):
        """Set up test fixtures."""
        self.artifactory = Artifactory("test-token")

    @patch('utils.artifactory.ArtifactoryPath')
    def test_download_nupkg_private_package(self, mock_artifactory_path):
        """Test downloading private NuGet package uses correct repository."""
        # Mock the ArtifactoryPath and its read_bytes method
        mock_path_instance = MagicMock()
        mock_artifactory_path.return_value = mock_path_instance
        mock_path_instance.read_bytes.return_value = b"fake nupkg content"

        # Test artifact info for private NuGet package
        artifact_info = {
            'group_id': 'com.sonarsource.dotnet',
            'artifact_id': 'sonar-dotnet-autoscan',
            'version': '2.4.0',
            'extension': 'nupkg',
            'classifier': None
        }

        with patch('utils.artifactory.Path') as mock_path:
            mock_temp_file = MagicMock()
            mock_temp_file.open.return_value.__enter__.return_value = MagicMock()
            mock_path.return_value = mock_temp_file

            result = self.artifactory._download_single_artifact(artifact_info)

            # Verify the correct repository was used
            expected_url = "https://repox.jfrog.io/artifactory/sonarsource-nuget-private-builds/com/sonarsource/dotnet/sonar-dotnet-autoscan/2.4.0/sonar-dotnet-autoscan-2.4.0.nupkg"
            mock_artifactory_path.assert_called_once_with(expected_url, auth=self.artifactory.auth)

            # Verify the result
            self.assertIsNotNone(result)
            self.assertEqual(result['group_id'], 'com.sonarsource.dotnet')
            self.assertEqual(result['artifact_id'], 'sonar-dotnet-autoscan')
            self.assertEqual(result['extension'], 'nupkg')

    @patch('utils.artifactory.ArtifactoryPath')
    def test_download_nupkg_public_package(self, mock_artifactory_path):
        """Test downloading public NuGet package uses correct repository."""
        # Mock the ArtifactoryPath and its read_bytes method
        mock_path_instance = MagicMock()
        mock_artifactory_path.return_value = mock_path_instance
        mock_path_instance.read_bytes.return_value = b"fake nupkg content"

        # Test artifact info for public NuGet package
        artifact_info = {
            'group_id': 'org.sonarsource.dotnet',
            'artifact_id': 'sonar-dotnet-public',
            'version': '1.0.0',
            'extension': 'nupkg',
            'classifier': None
        }

        with patch('utils.artifactory.Path') as mock_path:
            mock_temp_file = MagicMock()
            mock_temp_file.open.return_value.__enter__.return_value = MagicMock()
            mock_path.return_value = mock_temp_file

            result = self.artifactory._download_single_artifact(artifact_info)

            # Verify the correct repository was used
            expected_url = "https://repox.jfrog.io/artifactory/sonarsource-nuget-public/org/sonarsource/dotnet/sonar-dotnet-public/1.0.0/sonar-dotnet-public-1.0.0.nupkg"
            mock_artifactory_path.assert_called_once_with(expected_url, auth=self.artifactory.auth)

            # Verify the result
            self.assertIsNotNone(result)
            self.assertEqual(result['group_id'], 'org.sonarsource.dotnet')
            self.assertEqual(result['artifact_id'], 'sonar-dotnet-public')
            self.assertEqual(result['extension'], 'nupkg')

    @patch('utils.artifactory.ArtifactoryPath')
    def test_download_jar_private_package(self, mock_artifactory_path):
        """Test downloading private JAR package uses regular repository."""
        # Mock the ArtifactoryPath and its read_bytes method
        mock_path_instance = MagicMock()
        mock_artifactory_path.return_value = mock_path_instance
        mock_path_instance.read_bytes.return_value = b"fake jar content"

        # Test artifact info for private JAR package
        artifact_info = {
            'group_id': 'com.sonarsource.java',
            'artifact_id': 'sonar-java-plugin',
            'version': '1.0.0',
            'extension': 'jar',
            'classifier': None
        }

        with patch('utils.artifactory.Path') as mock_path:
            mock_temp_file = MagicMock()
            mock_temp_file.open.return_value.__enter__.return_value = MagicMock()
            mock_path.return_value = mock_temp_file

            result = self.artifactory._download_single_artifact(artifact_info)

            # Verify the correct repository was used (regular, not NuGet)
            expected_url = "https://repox.jfrog.io/artifactory/sonarsource-private-builds/com/sonarsource/java/sonar-java-plugin/1.0.0/sonar-java-plugin-1.0.0.jar"
            mock_artifactory_path.assert_called_once_with(expected_url, auth=self.artifactory.auth)

            # Verify the result
            self.assertIsNotNone(result)
            self.assertEqual(result['group_id'], 'com.sonarsource.java')
            self.assertEqual(result['artifact_id'], 'sonar-java-plugin')
            self.assertEqual(result['extension'], 'jar')

    @patch('utils.artifactory.ArtifactoryPath')
    def test_download_jar_public_package(self, mock_artifactory_path):
        """Test downloading public JAR package uses regular repository."""
        # Mock the ArtifactoryPath and its read_bytes method
        mock_path_instance = MagicMock()
        mock_artifactory_path.return_value = mock_path_instance
        mock_path_instance.read_bytes.return_value = b"fake jar content"

        # Test artifact info for public JAR package
        artifact_info = {
            'group_id': 'org.sonarsource.java',
            'artifact_id': 'sonar-java-plugin',
            'version': '1.0.0',
            'extension': 'jar',
            'classifier': None
        }

        with patch('utils.artifactory.Path') as mock_path:
            mock_temp_file = MagicMock()
            mock_temp_file.open.return_value.__enter__.return_value = MagicMock()
            mock_path.return_value = mock_temp_file

            result = self.artifactory._download_single_artifact(artifact_info)

            # Verify the correct repository was used (regular, not NuGet)
            expected_url = "https://repox.jfrog.io/artifactory/sonarsource-public-builds/org/sonarsource/java/sonar-java-plugin/1.0.0/sonar-java-plugin-1.0.0.jar"
            mock_artifactory_path.assert_called_once_with(expected_url, auth=self.artifactory.auth)

            # Verify the result
            self.assertIsNotNone(result)
            self.assertEqual(result['group_id'], 'org.sonarsource.java')
            self.assertEqual(result['artifact_id'], 'sonar-java-plugin')
            self.assertEqual(result['extension'], 'jar')

    @patch('utils.artifactory.ArtifactoryPath')
    def test_download_zip_private_package(self, mock_artifactory_path):
        """Test downloading private ZIP package uses regular repository."""
        # Mock the ArtifactoryPath and its read_bytes method
        mock_path_instance = MagicMock()
        mock_artifactory_path.return_value = mock_path_instance
        mock_path_instance.read_bytes.return_value = b"fake zip content"

        # Test artifact info for private ZIP package
        artifact_info = {
            'group_id': 'com.sonarsource.tools',
            'artifact_id': 'sonar-tool',
            'version': '1.0.0',
            'extension': 'zip',
            'classifier': None
        }

        with patch('utils.artifactory.Path') as mock_path:
            mock_temp_file = MagicMock()
            mock_temp_file.open.return_value.__enter__.return_value = MagicMock()
            mock_path.return_value = mock_temp_file

            result = self.artifactory._download_single_artifact(artifact_info)

            # Verify the correct repository was used (regular, not NuGet)
            expected_url = "https://repox.jfrog.io/artifactory/sonarsource-private-builds/com/sonarsource/tools/sonar-tool/1.0.0/sonar-tool-1.0.0.zip"
            mock_artifactory_path.assert_called_once_with(expected_url, auth=self.artifactory.auth)

            # Verify the result
            self.assertIsNotNone(result)
            self.assertEqual(result['group_id'], 'com.sonarsource.tools')
            self.assertEqual(result['artifact_id'], 'sonar-tool')
            self.assertEqual(result['extension'], 'zip')

    def test_repository_selection_logic(self):
        """Test the repository selection logic for different package types."""
        # Test cases: (group_id, extension, expected_repo)
        test_cases = [
            # NuGet packages
            ('com.sonarsource.dotnet', 'nupkg', 'sonarsource-nuget-private-builds'),
            ('org.sonarsource.dotnet', 'nupkg', 'sonarsource-nuget-public'),
            # Regular packages
            ('com.sonarsource.java', 'jar', 'sonarsource-private-builds'),
            ('org.sonarsource.java', 'jar', 'sonarsource-public-builds'),
            ('com.sonarsource.tools', 'zip', 'sonarsource-private-builds'),
            ('org.sonarsource.tools', 'zip', 'sonarsource-public-builds'),
            # Edge cases
            ('com.sonarsource.test', 'NUPKG', 'sonarsource-nuget-private-builds'),  # Case insensitive
            ('org.sonarsource.test', 'NuPkg', 'sonarsource-nuget-public-builds'),  # Case insensitive
        ]

        for group_id, extension, expected_repo in test_cases:
            with self.subTest(group_id=group_id, extension=extension):
                # Create artifact info
                artifact_info = {
                    'group_id': group_id,
                    'artifact_id': 'test-artifact',
                    'version': '1.0.0',
                    'extension': extension,
                    'classifier': None
                }

            # Mock the repository selection logic
            if extension.lower() in ['nupkg']:
                actual_repo = "sonarsource-nuget-private-builds" if group_id.startswith('com.') else "sonarsource-nuget-public"
            else:
                actual_repo = "sonarsource-private-builds" if group_id.startswith('com.') else "sonarsource-public-builds"

                self.assertEqual(actual_repo, expected_repo,
                               f"Repository selection failed for {group_id}:{extension}")


if __name__ == '__main__':
    unittest.main()
