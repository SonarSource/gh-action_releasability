import unittest
from unittest.mock import MagicMock

# Adjust path for local imports
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from utils.buildinfo import BuildInfo


class TestBuildInfo(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures."""
        self.sample_buildinfo = {
            'buildInfo': {
                'properties': {
                    'sonar.projectKey': 'org.sonarsource.javascript:javascript',
                    'buildInfo.env.ARTIFACTS_TO_PUBLISH': 'org.sonarsource:plugin:1.0.0:jar',
                    'custom.property': 'custom-value'
                },
                'modules': [
                    {
                        'id': 'org.sonarsource.javascript:javascript:11.4.0.34681',
                        'properties': {
                            'artifactsToPublish': 'org.sonarsource:plugin:1.0.0:jar',
                            'module.property': 'module-value'
                        }
                    }
                ],
                'statuses': [
                    {
                        'repository': 'sonarsource-public-releases'
                    }
                ]
            }
        }
        self.buildinfo = BuildInfo(self.sample_buildinfo)

    def test_init(self):
        """Test BuildInfo initialization."""
        self.assertEqual(self.buildinfo.json, self.sample_buildinfo)

    def test_get_property_success(self):
        """Test successful property retrieval."""
        result = self.buildinfo.get_property('sonar.projectKey')
        self.assertEqual(result, 'org.sonarsource.javascript:javascript')

    def test_get_property_with_default(self):
        """Test property retrieval with default value."""
        result = self.buildinfo.get_property('nonexistent.property', 'default-value')
        self.assertEqual(result, 'default-value')

    def test_get_property_missing_key(self):
        """Test property retrieval with missing key."""
        result = self.buildinfo.get_property('missing.property')
        self.assertIsNone(result)

    def test_get_module_property_success(self):
        """Test successful module property retrieval."""
        result = self.buildinfo.get_module_property('artifactsToPublish')
        self.assertEqual(result, 'org.sonarsource:plugin:1.0.0:jar')

    def test_get_module_property_with_default(self):
        """Test module property retrieval with default value."""
        result = self.buildinfo.get_module_property('nonexistent.property', 'default-value')
        self.assertEqual(result, 'default-value')

    def test_get_module_property_missing_key(self):
        """Test module property retrieval with missing key."""
        result = self.buildinfo.get_module_property('missing.property')
        self.assertIsNone(result)

    def test_get_module_property_no_modules(self):
        """Test module property retrieval with no modules."""
        buildinfo_data = {
            'buildInfo': {
                'modules': []
            }
        }
        buildinfo = BuildInfo(buildinfo_data)

        result = buildinfo.get_module_property('artifactsToPublish')
        self.assertIsNone(result)

    def test_get_version_success(self):
        """Test successful version retrieval."""
        result = self.buildinfo.get_version()
        self.assertEqual(result, '11.4.0.34681')

    def test_get_version_no_modules(self):
        """Test version retrieval with no modules."""
        buildinfo_data = {
            'buildInfo': {
                'modules': []
            }
        }
        buildinfo = BuildInfo(buildinfo_data)

        result = buildinfo.get_version()
        self.assertIsNone(result)

    def test_get_source_and_target_repos_revoke_false(self):
        """Test repository names when revoke is False."""
        source, target = self.buildinfo.get_source_and_target_repos(False)
        self.assertEqual(source, 'sonarsource-public-builds')
        self.assertEqual(target, 'sonarsource-public-releases')

    def test_get_source_and_target_repos_revoke_true(self):
        """Test repository names when revoke is True."""
        source, target = self.buildinfo.get_source_and_target_repos(True)
        self.assertEqual(source, 'sonarsource-public-releases')
        self.assertEqual(target, 'sonarsource-public-builds')

    def test_get_source_and_target_repos_no_statuses(self):
        """Test repository names with no statuses."""
        buildinfo_data = {
            'buildInfo': {
                'statuses': []
            }
        }
        buildinfo = BuildInfo(buildinfo_data)

        source, target = buildinfo.get_source_and_target_repos(False)
        self.assertIsNone(source)
        self.assertIsNone(target)

    def test_get_artifacts_to_publish_from_module(self):
        """Test artifacts to publish retrieval from module properties."""
        result = self.buildinfo.get_artifacts_to_publish()
        self.assertEqual(result, 'org.sonarsource:plugin:1.0.0:jar')

    def test_get_artifacts_to_publish_from_buildinfo(self):
        """Test artifacts to publish retrieval from build info properties."""
        buildinfo_data = {
            'buildInfo': {
                'modules': [
                    {
                        'id': 'org.sonarsource.javascript:javascript:11.4.0.34681',
                        'properties': {}
                    }
                ],
                'properties': {
                    'buildInfo.env.ARTIFACTS_TO_PUBLISH': 'org.sonarsource:plugin:1.0.0:jar'
                }
            }
        }
        buildinfo = BuildInfo(buildinfo_data)

        result = buildinfo.get_artifacts_to_publish()
        self.assertEqual(result, 'org.sonarsource:plugin:1.0.0:jar')

    def test_get_artifacts_to_publish_none(self):
        """Test artifacts to publish retrieval when none exist."""
        buildinfo_data = {
            'buildInfo': {
                'modules': [
                    {
                        'id': 'org.sonarsource.javascript:javascript:11.4.0.34681',
                        'properties': {}
                    }
                ],
                'properties': {}
            }
        }
        buildinfo = BuildInfo(buildinfo_data)

        result = buildinfo.get_artifacts_to_publish()
        self.assertIsNone(result)

    def test_is_public_true(self):
        """Test is_public when artifacts contain org.sonarsource."""
        result = self.buildinfo.is_public()
        self.assertTrue(result)

    def test_is_public_false(self):
        """Test is_public when artifacts don't contain org.sonarsource."""
        buildinfo_data = {
            'buildInfo': {
                'modules': [
                    {
                        'id': 'org.sonarsource.javascript:javascript:11.4.0.34681',
                        'properties': {
                            'artifactsToPublish': 'com.sonarsource:private-plugin:1.0.0:jar'
                        }
                    }
                ]
            }
        }
        buildinfo = BuildInfo(buildinfo_data)

        result = buildinfo.is_public()
        self.assertFalse(result)

    def test_is_public_no_artifacts(self):
        """Test is_public when no artifacts exist."""
        buildinfo_data = {
            'buildInfo': {
                'modules': [
                    {
                        'id': 'org.sonarsource.javascript:javascript:11.4.0.34681',
                        'properties': {}
                    }
                ]
            }
        }
        buildinfo = BuildInfo(buildinfo_data)

        result = buildinfo.is_public()
        self.assertFalse(result)

    def test_get_package_success(self):
        """Test successful package retrieval."""
        result = self.buildinfo.get_package()
        self.assertEqual(result, 'org.sonarsource')

    def test_get_package_no_artifacts(self):
        """Test package retrieval with no artifacts."""
        buildinfo_data = {
            'buildInfo': {
                'modules': [
                    {
                        'id': 'org.sonarsource.javascript:javascript:11.4.0.34681',
                        'properties': {}
                    }
                ]
            }
        }
        buildinfo = BuildInfo(buildinfo_data)

        result = buildinfo.get_package()
        self.assertIsNone(result)

    def test_get_package_empty_artifacts(self):
        """Test package retrieval with empty artifacts string."""
        buildinfo_data = {
            'buildInfo': {
                'modules': [
                    {
                        'id': 'org.sonarsource.javascript:javascript:11.4.0.34681',
                        'properties': {
                            'artifactsToPublish': ''
                        }
                    }
                ]
            }
        }
        buildinfo = BuildInfo(buildinfo_data)

        result = buildinfo.get_package()
        self.assertIsNone(result)

    def test_get_package_multiple_artifacts(self):
        """Test package retrieval with multiple artifacts (should return first)."""
        buildinfo_data = {
            'buildInfo': {
                'modules': [
                    {
                        'id': 'org.sonarsource.javascript:javascript:11.4.0.34681',
                        'properties': {
                            'artifactsToPublish': 'org.sonarsource:plugin1:1.0.0:jar,com.sonarsource:plugin2:2.0.0:jar'
                        }
                    }
                ]
            }
        }
        buildinfo = BuildInfo(buildinfo_data)

        result = buildinfo.get_package()
        self.assertEqual(result, 'org.sonarsource')

    def test_get_package_invalid_format(self):
        """Test package retrieval with invalid artifact format."""
        buildinfo_data = {
            'buildInfo': {
                'modules': [
                    {
                        'id': 'org.sonarsource.javascript:javascript:11.4.0.34681',
                        'properties': {
                            'artifactsToPublish': 'invalid-format'
                        }
                    }
                ]
            }
        }
        buildinfo = BuildInfo(buildinfo_data)

        result = buildinfo.get_package()
        self.assertIsNone(result)

    def test_get_package_single_artifact_no_colon(self):
        """Test package retrieval with single artifact but no colon separator."""
        buildinfo_data = {
            'buildInfo': {
                'modules': [
                    {
                        'id': 'org.sonarsource.javascript:javascript:11.4.0.34681',
                        'properties': {
                            'artifactsToPublish': 'single-artifact'
                        }
                    }
                ]
            }
        }
        buildinfo = BuildInfo(buildinfo_data)

        result = buildinfo.get_package()
        self.assertIsNone(result)

    def test_get_package_empty_artifact_list(self):
        """Test package retrieval with empty artifact list."""
        buildinfo_data = {
            'buildInfo': {
                'modules': [
                    {
                        'id': 'org.sonarsource.javascript:javascript:11.4.0.34681',
                        'properties': {
                            'artifactsToPublish': ','
                        }
                    }
                ]
            }
        }
        buildinfo = BuildInfo(buildinfo_data)

        result = buildinfo.get_package()
        self.assertIsNone(result)

    def test_get_package_whitespace_handling(self):
        """Test package retrieval with whitespace in artifacts."""
        buildinfo_data = {
            'buildInfo': {
                'modules': [
                    {
                        'id': 'org.sonarsource.javascript:javascript:11.4.0.34681',
                        'properties': {
                            'artifactsToPublish': '  org.sonarsource:plugin:1.0.0:jar  '
                        }
                    }
                ]
            }
        }
        buildinfo = BuildInfo(buildinfo_data)

        result = buildinfo.get_package()
        self.assertEqual(result, 'org.sonarsource')

    def test_get_package_complex_artifact_format(self):
        """Test package retrieval with complex artifact format (groupId:artifactId:version:extension:classifier)."""
        buildinfo_data = {
            'buildInfo': {
                'modules': [
                    {
                        'id': 'org.sonarsource.javascript:javascript:11.4.0.34681',
                        'properties': {
                            'artifactsToPublish': 'org.sonarsource:plugin:1.0.0:jar:sources'
                        }
                    }
                ]
            }
        }
        buildinfo = BuildInfo(buildinfo_data)

        result = buildinfo.get_package()
        self.assertEqual(result, 'org.sonarsource')


if __name__ == '__main__':
    unittest.main()
