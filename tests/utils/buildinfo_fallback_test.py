"""
Tests for BuildInfo fallback artifact functionality.
"""

import unittest
import json
from unittest.mock import MagicMock

# Adjust path for local imports
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from utils.buildinfo import BuildInfo


class TestBuildInfoFallback(unittest.TestCase):
    """Test cases for BuildInfo fallback artifact functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Load real buildinfo.json for testing
        buildinfo_path = os.path.join(os.path.dirname(__file__), '../resources/buildinfo.json')
        with open(buildinfo_path, 'r') as f:
            self.real_buildinfo = json.load(f)

        self.sample_buildinfo_public = {
            'buildInfo': {
                'modules': [
                {
                    'id': 'org.sonarsource.javascript:javascript:11.4.0.34681',
                    'properties': {
                        'artifactsToPublish': ''  # Empty artifacts to publish
                    },
                    'artifacts': [
                        {
                            'name': 'sonar-javascript-plugin-11.4.0.34681.jar',
                            'type': 'jar',
                            'path': 'org/sonarsource/javascript/sonar-javascript-plugin/11.4.0.34681/sonar-javascript-plugin-11.4.0.34681.jar',
                            'sha1': 'abc123',
                            'md5': 'def456'
                        },
                        {
                            'name': 'sonar-javascript-plugin-11.4.0.34681-sources.jar',
                            'type': 'jar',
                            'path': 'org/sonarsource/javascript/sonar-javascript-plugin/11.4.0.34681/sonar-javascript-plugin-11.4.0.34681-sources.jar',
                            'sha1': 'ghi789',
                            'md5': 'jkl012'
                        }
                    ]
                }
            ]
            }
        }

        self.sample_buildinfo_private = {
            'buildInfo': {
                'modules': [
                {
                    'id': 'com.sonarsource.internal:internal-plugin:2.0.0.12345',
                    'properties': {
                        'artifactsToPublish': ''  # Empty artifacts to publish
                    },
                    'artifacts': [
                        {
                            'name': 'internal-plugin-2.0.0.12345.jar',
                            'type': 'jar',
                            'path': 'com/sonarsource/internal/internal-plugin/2.0.0.12345/internal-plugin-2.0.0.12345.jar',
                            'sha1': 'mno345',
                            'md5': 'pqr678'
                        },
                        {
                            'name': 'internal-plugin-2.0.0.12345-javadoc.jar',
                            'type': 'jar',
                            'path': 'com/sonarsource/internal/internal-plugin/2.0.0.12345/internal-plugin-2.0.0.12345-javadoc.jar',
                            'sha1': 'stu901',
                            'md5': 'vwx234'
                        }
                    ]
                }
            ]
            }
        }

        self.sample_buildinfo_no_artifacts = {
            'buildInfo': {
                'modules': [
                {
                    'id': 'org.sonarsource.test:test:1.0.0',
                    'properties': {
                        'artifactsToPublish': ''
                    },
                    'artifacts': []  # No artifacts
                }
            ]
            }
        }

        self.sample_buildinfo_no_jar_artifacts = {
            'buildInfo': {
                'modules': [
                {
                    'id': 'org.sonarsource.test:test:1.0.0',
                    'properties': {
                        'artifactsToPublish': ''
                    },
                    'artifacts': [
                        {
                            'name': 'test-plugin.zip',
                            'type': 'zip',
                            'path': 'org/sonarsource/test/test-plugin/1.0.0/test-plugin.zip',
                            'sha1': 'abc123',
                            'md5': 'def456'
                        }
                    ]
                }
            ]
            }
        }

    def test_get_first_suitable_artifact_real_buildinfo(self):
        """Test finding suitable artifact using real buildinfo.json."""
        # The real buildinfo.json has a different structure - modules are directly under root
        # We need to wrap it in the buildInfo structure for the test
        wrapped_buildinfo = {'buildInfo': self.real_buildinfo}
        buildinfo = BuildInfo(wrapped_buildinfo)

        result = buildinfo.get_first_suitable_artifact(is_public=False)

        # Should return the NUPKG artifact from the real buildinfo
        self.assertEqual(result, 'com.sonarsource:sonar-dotnet-autoscan:2.4.0:nupkg:AutoScan.NET.2.4.0.124996.nupkg:sonarsource-nuget-private-qa')

    def test_get_first_suitable_artifact_public_project(self):
        """Test finding suitable artifact for public project."""
        buildinfo = BuildInfo(self.sample_buildinfo_public)

        result = buildinfo.get_first_suitable_artifact(is_public=True)

        # Should return the main JAR, not the sources JAR
        # The module ID is 'org.sonarsource.javascript:javascript:11.4.0.34681'
        self.assertEqual(result, 'org.sonarsource.javascript:javascript:11.4.0.34681:jar:sonar-javascript-plugin-11.4.0.34681.jar')

    def test_get_first_suitable_artifact_private_project(self):
        """Test finding suitable artifact for private project."""
        buildinfo = BuildInfo(self.sample_buildinfo_private)

        result = buildinfo.get_first_suitable_artifact(is_public=False)

        # Should return the main JAR, not the javadoc JAR
        # The module ID is 'com.sonarsource.internal:internal-plugin:2.0.0.12345'
        self.assertEqual(result, 'com.sonarsource.internal:internal-plugin:2.0.0.12345:jar:internal-plugin-2.0.0.12345.jar')

    def test_get_first_suitable_artifact_auto_detect_public(self):
        """Test auto-detection of public project."""
        buildinfo = BuildInfo(self.sample_buildinfo_public)

        result = buildinfo.get_first_suitable_artifact()

        # Should auto-detect as public and return appropriate artifact
        # The module ID is 'org.sonarsource.javascript:javascript:11.4.0.34681'
        self.assertEqual(result, 'org.sonarsource.javascript:javascript:11.4.0.34681:jar:sonar-javascript-plugin-11.4.0.34681.jar')

    def test_get_first_suitable_artifact_no_artifacts(self):
        """Test when no artifacts are available."""
        buildinfo = BuildInfo(self.sample_buildinfo_no_artifacts)

        result = buildinfo.get_first_suitable_artifact()

        self.assertIsNone(result)

    def test_get_first_suitable_artifact_no_supported_artifacts(self):
        """Test when no supported artifacts (JAR/NUPKG) are available."""
        buildinfo = BuildInfo(self.sample_buildinfo_no_jar_artifacts)

        result = buildinfo.get_first_suitable_artifact()

        self.assertIsNone(result)

    def test_is_suitable_artifact_jar_file(self):
        """Test that JAR files are considered suitable."""
        buildinfo = BuildInfo(self.sample_buildinfo_public)

        artifact = {
            'name': 'test-plugin.jar',
            'type': 'jar',
            'path': 'org/sonarsource/test/test-plugin/1.0.0/test-plugin.jar'
        }

        result = buildinfo._is_suitable_artifact(artifact)
        self.assertTrue(result)

    def test_is_suitable_artifact_nupkg_file(self):
        """Test that NUPKG files are considered suitable."""
        buildinfo = BuildInfo(self.sample_buildinfo_public)

        artifact = {
            'name': 'test-plugin.nupkg',
            'type': 'nupkg',
            'path': 'com/sonarsource/test/test-plugin/1.0.0/test-plugin.nupkg'
        }

        result = buildinfo._is_suitable_artifact(artifact)
        self.assertTrue(result)

    def test_is_suitable_artifact_non_supported_file(self):
        """Test that non-supported files are not considered suitable."""
        buildinfo = BuildInfo(self.sample_buildinfo_public)

        artifact = {
            'name': 'test-plugin.zip',
            'type': 'zip',
            'path': 'org/sonarsource/test/test-plugin/1.0.0/test-plugin.zip'
        }

        result = buildinfo._is_suitable_artifact(artifact)
        self.assertFalse(result)

    def test_is_suitable_artifact_sources_jar(self):
        """Test that sources JARs are not considered suitable."""
        buildinfo = BuildInfo(self.sample_buildinfo_public)

        artifact = {
            'name': 'test-plugin-sources.jar',
            'type': 'jar',
            'path': 'org/sonarsource/test/test-plugin/1.0.0/test-plugin-sources.jar'
        }

        result = buildinfo._is_suitable_artifact(artifact)
        self.assertFalse(result)

    def test_is_suitable_artifact_javadoc_jar(self):
        """Test that javadoc JARs are not considered suitable."""
        buildinfo = BuildInfo(self.sample_buildinfo_public)

        artifact = {
            'name': 'test-plugin-javadoc.jar',
            'type': 'jar',
            'path': 'org/sonarsource/test/test-plugin/1.0.0/test-plugin-javadoc.jar'
        }

        result = buildinfo._is_suitable_artifact(artifact)
        self.assertFalse(result)

    def test_is_suitable_artifact_sources_in_name(self):
        """Test that JARs with 'sources' in the name are not considered suitable."""
        buildinfo = BuildInfo(self.sample_buildinfo_public)

        artifact = {
            'name': 'sources-test-plugin.jar',
            'type': 'jar',
            'path': 'org/sonarsource/test/sources-test-plugin/1.0.0/sources-test-plugin.jar'
        }

        result = buildinfo._is_suitable_artifact(artifact)
        self.assertFalse(result)

    def test_is_suitable_artifact_javadoc_in_name(self):
        """Test that JARs with 'javadoc' in the name are not considered suitable."""
        buildinfo = BuildInfo(self.sample_buildinfo_public)

        artifact = {
            'name': 'javadoc-test-plugin.jar',
            'type': 'jar',
            'path': 'org/sonarsource/test/javadoc-test-plugin/1.0.0/javadoc-test-plugin.jar'
        }

        result = buildinfo._is_suitable_artifact(artifact)
        self.assertFalse(result)

    def test_get_first_suitable_artifact_with_version_fallback(self):
        """Test that version fallback works when module version is not available."""
        buildinfo_data = {
            'buildInfo': {
                'modules': [
                {
                    'id': 'org.sonarsource.test:test',  # No version in ID
                    'properties': {
                        'artifactsToPublish': ''
                    },
                    'artifacts': [
                        {
                            'name': 'test-plugin.jar',
                            'type': 'jar',
                            'path': 'org/sonarsource/test/test-plugin/1.0.0/test-plugin.jar'
                        }
                    ]
                }
            ]
            }
        }
        buildinfo = BuildInfo(buildinfo_data)

        result = buildinfo.get_first_suitable_artifact(is_public=True)

        # Should use fallback version
        self.assertEqual(result, 'org.sonarsource:test-plugin:test:jar:test-plugin.jar')

    def test_get_first_suitable_artifact_multiple_modules(self):
        """Test finding suitable artifact when multiple modules exist."""
        buildinfo_data = {
            'buildInfo': {
                'modules': [
                {
                    'id': 'org.sonarsource.module1:module1:1.0.0',
                    'properties': {'artifactsToPublish': ''},
                    'artifacts': [
                        {
                            'name': 'module1-sources.jar',
                            'type': 'jar',
                            'path': 'org/sonarsource/module1/module1/1.0.0/module1-sources.jar'
                        }
                    ]
                },
                {
                    'id': 'org.sonarsource.module2:module2:2.0.0',
                    'properties': {'artifactsToPublish': ''},
                    'artifacts': [
                        {
                            'name': 'module2.jar',
                            'type': 'jar',
                            'path': 'org/sonarsource/module2/module2/2.0.0/module2.jar'
                        }
                    ]
                }
            ]
            }
        }
        buildinfo = BuildInfo(buildinfo_data)

        result = buildinfo.get_first_suitable_artifact(is_public=True)

        # Should find the first suitable artifact (module2.jar)
        self.assertEqual(result, 'org.sonarsource.module2:module2:2.0.0:jar:module2.jar')

    def test_get_first_suitable_artifact_error_handling(self):
        """Test error handling in get_first_suitable_artifact."""
        # Create a buildinfo with malformed data that will cause an exception
        buildinfo_data = {
            'buildInfo': {
                'modules': [
                    {
                        'id': 'org.sonarsource.test:test:1.0.0',
                        'properties': {'artifactsToPublish': ''},
                        'artifacts': [
                            {
                                'name': 'test-plugin.jar',
                                'type': 'jar'
                                # Missing other required fields
                            }
                        ]
                    }
                ]
            }
        }
        buildinfo = BuildInfo(buildinfo_data)

        result = buildinfo.get_first_suitable_artifact(is_public=True)

        # The method should handle the data gracefully and return the artifact
        # Even with minimal data, it should work
        self.assertEqual(result, 'org.sonarsource.test:test:1.0.0:jar:test-plugin.jar')


if __name__ == '__main__':
    unittest.main()
