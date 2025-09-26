import unittest
import os
import json
from unittest.mock import patch, MagicMock, Mock

# Adjust path for local imports
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from utils.sonarqube import SonarQube


class TestSonarQube(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures."""
        self.sonarqube = SonarQube(base_url="https://test.sonarqube.com", token="test-token")
        self.sample_sbom_data = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.6",
            "serialNumber": "urn:uuid:12345678-1234-1234-1234-123456789012",
            "components": [
                {
                    "name": "test-package",
                    "version": "1.0.0",
                    "purl": "pkg:npm/test-package@1.0.0"
                },
                {
                    "name": "another-package",
                    "version": "2.0.0",
                    "purl": "pkg:npm/another-package@2.0.0"
                }
            ]
        }

    def test_init(self):
        """Test SonarQube initialization."""
        self.assertEqual(self.sonarqube.base_url, "https://test.sonarqube.com")
        self.assertEqual(self.sonarqube.token, "test-token")
        self.assertEqual(self.sonarqube.headers['Authorization'], "Bearer test-token")
        self.assertEqual(self.sonarqube.headers['Content-Type'], "application/json")

    def test_init_strips_trailing_slash(self):
        """Test that initialization strips trailing slash from base URL."""
        sonarqube = SonarQube(base_url="https://test.sonarqube.com/", token="test-token")
        self.assertEqual(sonarqube.base_url, "https://test.sonarqube.com")

    @patch('utils.sonarqube.requests.get')
    def test_download_sbom_success(self, mock_get):
        """Test successful SBOM download."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.sample_sbom_data
        mock_get.return_value = mock_response

        result = self.sonarqube.download_sbom("org.test:component", "master", "cyclonedx")

        # Verify the request was made correctly
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        self.assertEqual(call_args[1]['headers']['Accept'], 'application/vnd.cyclonedx+json')
        self.assertEqual(call_args[1]['params']['component'], 'org.test:component')
        self.assertEqual(call_args[1]['params']['branch'], 'master')
        self.assertEqual(call_args[1]['params']['type'], 'cyclonedx')

        # Verify the result
        self.assertEqual(result, self.sample_sbom_data)

    @patch('utils.sonarqube.requests.get')
    def test_download_sbom_spdx_format(self, mock_get):
        """Test SBOM download with SPDX format."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"spdxVersion": "SPDX-2.3"}
        mock_get.return_value = mock_response

        result = self.sonarqube.download_sbom("org.test:component", "master", "spdx_23")

        # Verify SPDX Accept header
        call_args = mock_get.call_args
        self.assertEqual(call_args[1]['headers']['Accept'], 'application/spdx+json')

    @patch('utils.sonarqube.requests.get')
    def test_download_sbom_http_error(self, mock_get):
        """Test SBOM download with HTTP error."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Component not found"
        mock_get.return_value = mock_response

        result = self.sonarqube.download_sbom("org.test:nonexistent", "master")

        self.assertIsNone(result)

    @patch('utils.sonarqube.requests.get')
    def test_download_sbom_request_exception(self, mock_get):
        """Test SBOM download with request exception."""
        mock_get.side_effect = Exception("Network error")

        result = self.sonarqube.download_sbom("org.test:component", "master")

        self.assertIsNone(result)

    @patch('utils.sonarqube.requests.get')
    def test_download_sbom_json_decode_error(self, mock_get):
        """Test SBOM download with JSON decode error."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "doc", 0)
        mock_get.return_value = mock_response

        result = self.sonarqube.download_sbom("org.test:component", "master")

        self.assertIsNone(result)

    @patch.dict(os.environ, {'SONAR_PROJECT_KEY': 'org.sonarsource.javascript:javascript'})
    def test_get_project_key_from_env_success(self):
        """Test successful project key extraction from environment variable."""
        result = self.sonarqube.get_project_key_from_env()

        self.assertEqual(result, "org.sonarsource.javascript:javascript")

    @patch.dict(os.environ, {}, clear=True)
    def test_get_project_key_from_env_not_set(self):
        """Test project key extraction when environment variable is not set."""
        result = self.sonarqube.get_project_key_from_env()

        self.assertIsNone(result)

    @patch.dict(os.environ, {'SONAR_PROJECT_KEY': ''})
    def test_get_project_key_from_env_empty(self):
        """Test project key extraction when environment variable is empty."""
        result = self.sonarqube.get_project_key_from_env()

        self.assertIsNone(result)

    @patch('utils.sonarqube.requests.get')
    def test_download_sbom_timeout(self, mock_get):
        """Test SBOM download with timeout."""
        mock_get.side_effect = Exception("Timeout")

        result = self.sonarqube.download_sbom("org.test:component", "master")

        self.assertIsNone(result)

    def test_download_sbom_default_parameters(self):
        """Test SBOM download with default parameters."""
        with patch('utils.sonarqube.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = self.sample_sbom_data
            mock_get.return_value = mock_response

            result = self.sonarqube.download_sbom("org.test:component")

            # Verify default parameters
            call_args = mock_get.call_args
            self.assertEqual(call_args[1]['params']['branch'], 'master')
            self.assertEqual(call_args[1]['params']['type'], 'cyclonedx')

    def test_download_sbom_url_construction(self):
        """Test that the correct URL is constructed."""
        with patch('utils.sonarqube.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = self.sample_sbom_data
            mock_get.return_value = mock_response

            self.sonarqube.download_sbom("org.test:component", "feature-branch", "cyclonedx")

            # Verify URL construction
            call_args = mock_get.call_args
            expected_url = "https://test.sonarqube.com/sonarqube/api/v2/sca/sbom-reports"
            self.assertEqual(call_args[0][0], expected_url)

    def test_download_sbom_headers_preservation(self):
        """Test that original headers are preserved when adding Accept header."""
        with patch('utils.sonarqube.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = self.sample_sbom_data
            mock_get.return_value = mock_response

            self.sonarqube.download_sbom("org.test:component")

            # Verify headers
            call_args = mock_get.call_args
            headers = call_args[1]['headers']
            self.assertEqual(headers['Authorization'], "Bearer test-token")
            self.assertEqual(headers['Content-Type'], "application/json")
            self.assertEqual(headers['Accept'], "application/vnd.cyclonedx+json")


if __name__ == '__main__':
    unittest.main()
