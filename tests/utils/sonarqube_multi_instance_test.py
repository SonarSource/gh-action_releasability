"""
Tests for multi-instance SonarQube functionality.
"""

import unittest
import os
from unittest.mock import Mock, patch, MagicMock
import requests

from utils.sonarqube import SonarQube


class TestSonarQubeMultiInstance(unittest.TestCase):
    """Test cases for multi-instance SonarQube functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.sample_sbom_data = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.4",
            "components": [
                {"name": "test-component", "version": "1.0.0"}
            ]
        }

    def test_instance_configurations(self):
        """Test that all instance configurations are properly defined."""
        instances = SonarQube.get_available_instances()
        expected_instances = ["next", "sonarcloud", "sonarqube.us"]
        self.assertEqual(set(instances), set(expected_instances))

        # Test each instance configuration
        for instance in expected_instances:
            config = SonarQube.get_instance_config(instance)
            self.assertIsNotNone(config)
            self.assertIn("url", config)
            self.assertIn("api_url", config)
            self.assertIn("token_env", config)
            self.assertIn("supports_sbom", config)

    def test_next_instance_config(self):
        """Test next instance configuration."""
        config = SonarQube.get_instance_config("next")
        self.assertEqual(config["url"], "https://next.sonarqube.com")
        self.assertEqual(config["api_url"], "https://next.sonarqube.com/sonarqube/api/v2/sca/sbom-reports")
        self.assertEqual(config["token_env"], "SONARQUBE_TOKEN")
        self.assertTrue(config["supports_sbom"])

    def test_sonarcloud_instance_config(self):
        """Test sonarcloud instance configuration."""
        config = SonarQube.get_instance_config("sonarcloud")
        self.assertEqual(config["url"], "https://sonarcloud.io")
        self.assertEqual(config["api_url"], "https://api.sonarcloud.io/sca/sbom-reports")
        self.assertEqual(config["token_env"], "SONARCLOUD_TOKEN")
        self.assertTrue(config["supports_sbom"])

    def test_sonarqube_us_instance_config(self):
        """Test sonarqube.us instance configuration."""
        config = SonarQube.get_instance_config("sonarqube.us")
        self.assertEqual(config["url"], "https://sonarqube.us")
        self.assertEqual(config["api_url"], "https://sonarqube.us/sonarqube/api/v2/sca/sbom-reports")
        self.assertEqual(config["token_env"], "SONARQUBE_US_TOKEN")
        self.assertFalse(config["supports_sbom"])

    def test_init_with_instance_name(self):
        """Test initialization with instance name."""
        with patch.dict(os.environ, {'SONARQUBE_TOKEN': 'test_token'}):
            client = SonarQube(instance="next")
            self.assertEqual(client.base_url, "https://next.sonarqube.com")
            self.assertEqual(client.api_url, "https://next.sonarqube.com/sonarqube/api/v2/sca/sbom-reports")
            self.assertTrue(client.supports_sbom)
            self.assertEqual(client.token, "test_token")

    def test_init_with_sonarcloud_instance(self):
        """Test initialization with sonarcloud instance."""
        with patch.dict(os.environ, {'SONARCLOUD_TOKEN': 'sonarcloud_token'}):
            client = SonarQube(instance="sonarcloud")
            self.assertEqual(client.base_url, "https://sonarcloud.io")
            self.assertEqual(client.api_url, "https://api.sonarcloud.io/sca/sbom-reports")
            self.assertTrue(client.supports_sbom)
            self.assertEqual(client.token, "sonarcloud_token")

    def test_init_with_sonarqube_us_instance(self):
        """Test initialization with sonarqube.us instance."""
        with patch.dict(os.environ, {'SONARQUBE_US_TOKEN': 'us_token'}):
            client = SonarQube(instance="sonarqube.us")
            self.assertEqual(client.base_url, "https://sonarqube.us")
            self.assertEqual(client.api_url, "https://sonarqube.us/sonarqube/api/v2/sca/sbom-reports")
            self.assertFalse(client.supports_sbom)
            self.assertEqual(client.token, "us_token")

    def test_init_with_invalid_instance(self):
        """Test initialization with invalid instance name."""
        with self.assertRaises(ValueError) as context:
            SonarQube(instance="invalid_instance")
        self.assertIn("Either instance name or both base_url and token must be provided", str(context.exception))

    def test_init_without_token(self):
        """Test initialization without token."""
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError) as context:
                SonarQube(instance="next")
            self.assertIn("SONARQUBE_TOKEN environment variable not set", str(context.exception))

    def test_init_with_manual_config(self):
        """Test initialization with manual configuration."""
        client = SonarQube(base_url="https://custom.sonarqube.com", token="custom_token")
        self.assertEqual(client.base_url, "https://custom.sonarqube.com")
        self.assertEqual(client.api_url, "https://custom.sonarqube.com/sonarqube/api/v2/sca/sbom-reports")
        self.assertTrue(client.supports_sbom)
        self.assertEqual(client.token, "custom_token")

    def test_init_with_manual_config_missing_params(self):
        """Test initialization with manual configuration missing parameters."""
        with self.assertRaises(ValueError) as context:
            SonarQube(base_url="https://custom.sonarqube.com")
        self.assertIn("Either instance name or both base_url and token must be provided", str(context.exception))

    @patch('utils.sonarqube.requests.get')
    def test_download_sbom_next_instance(self, mock_get):
        """Test SBOM download from next instance."""
        with patch.dict(os.environ, {'SONARQUBE_TOKEN': 'test_token'}):
            client = SonarQube(instance="next")

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = self.sample_sbom_data
            mock_get.return_value = mock_response

            result = client.download_sbom("org.test:component", "master", "cyclonedx")

            self.assertEqual(result, self.sample_sbom_data)
            mock_get.assert_called_once()
            call_args = mock_get.call_args
            self.assertEqual(call_args[0][0], "https://next.sonarqube.com/sonarqube/api/v2/sca/sbom-reports")

    @patch('utils.sonarqube.requests.get')
    def test_download_sbom_sonarcloud_instance(self, mock_get):
        """Test SBOM download from sonarcloud instance."""
        with patch.dict(os.environ, {'SONARCLOUD_TOKEN': 'sonarcloud_token'}):
            client = SonarQube(instance="sonarcloud")

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = self.sample_sbom_data
            mock_get.return_value = mock_response

            result = client.download_sbom("org.test:component", "master", "cyclonedx")

            self.assertEqual(result, self.sample_sbom_data)
            mock_get.assert_called_once()
            call_args = mock_get.call_args
            self.assertEqual(call_args[0][0], "https://api.sonarcloud.io/sca/sbom-reports")

    def test_download_sbom_sonarqube_us_no_support(self):
        """Test SBOM download from sonarqube.us instance (no SBOM support)."""
        with patch.dict(os.environ, {'SONARQUBE_US_TOKEN': 'us_token'}):
            client = SonarQube(instance="sonarqube.us")

            result = client.download_sbom("org.test:component", "master", "cyclonedx")

            self.assertIsNone(result)

    @patch('utils.sonarqube.requests.get')
    def test_download_sbom_with_spdx_format(self, mock_get):
        """Test SBOM download with SPDX format."""
        with patch.dict(os.environ, {'SONARQUBE_TOKEN': 'test_token'}):
            client = SonarQube(instance="next")

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"spdxVersion": "SPDX-2.3"}
            mock_get.return_value = mock_response

            result = client.download_sbom("org.test:component", "master", "spdx_23")

            self.assertEqual(result, {"spdxVersion": "SPDX-2.3"})
            call_args = mock_get.call_args
            headers = call_args[1]['headers']
            self.assertEqual(headers['Accept'], 'application/spdx+json')

    @patch('utils.sonarqube.requests.get')
    def test_download_sbom_http_error(self, mock_get):
        """Test SBOM download with HTTP error."""
        with patch.dict(os.environ, {'SONARQUBE_TOKEN': 'test_token'}):
            client = SonarQube(instance="next")

            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.text = "Not Found"
            mock_get.return_value = mock_response

            result = client.download_sbom("org.test:nonexistent", "master")

            self.assertIsNone(result)

    @patch('utils.sonarqube.requests.get')
    def test_download_sbom_request_exception(self, mock_get):
        """Test SBOM download with request exception."""
        with patch.dict(os.environ, {'SONARQUBE_TOKEN': 'test_token'}):
            client = SonarQube(instance="next")

            mock_get.side_effect = requests.exceptions.RequestException("Network error")

            result = client.download_sbom("org.test:component", "master")

            self.assertIsNone(result)

    @patch('utils.sonarqube.requests.get')
    def test_download_sbom_json_decode_error(self, mock_get):
        """Test SBOM download with JSON decode error."""
        with patch.dict(os.environ, {'SONARQUBE_TOKEN': 'test_token'}):
            client = SonarQube(instance="next")

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.side_effect = ValueError("Invalid JSON")
            mock_get.return_value = mock_response

            result = client.download_sbom("org.test:component", "master")

            self.assertIsNone(result)

    def test_get_project_key_from_env(self):
        """Test getting project key from environment variable."""
        with patch.dict(os.environ, {'SONAR_PROJECT_KEY': 'org.test:project'}):
            with patch.dict(os.environ, {'SONARQUBE_TOKEN': 'test_token'}):
                client = SonarQube(instance="next")
                result = client.get_project_key_from_env()
                self.assertEqual(result, "org.test:project")

    def test_get_project_key_from_env_not_set(self):
        """Test getting project key when environment variable is not set."""
        with patch.dict(os.environ, {}, clear=True):
            with patch.dict(os.environ, {'SONARQUBE_TOKEN': 'test_token'}):
                client = SonarQube(instance="next")
                result = client.get_project_key_from_env()
                self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
