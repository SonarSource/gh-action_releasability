"""
Tests for GitHub client functionality.
"""

import unittest
import json
import base64
from unittest.mock import Mock, patch, MagicMock
from github import GithubException

from utils.github_client import GitHubClient


class TestGitHubClient(unittest.TestCase):
    """Test cases for GitHubClient."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_token = "test_token_123"
        self.test_owner = "test-org"
        self.test_repo = "test-repo"
        self.test_file_path = ".sca-exceptions/false-positives.json"
        self.test_ref = "master"

    def test_init_with_token(self):
        """Test initialization with provided token."""
        client = GitHubClient(token=self.test_token)
        self.assertEqual(client.token, self.test_token)
        self.assertIsNotNone(client.github)

    def test_init_with_env_token(self):
        """Test initialization with token from environment variable."""
        with patch.dict('os.environ', {'GH_TOKEN': 'env_token_456'}):
            client = GitHubClient()
            self.assertEqual(client.token, 'env_token_456')
            self.assertIsNotNone(client.github)

    def test_init_without_token(self):
        """Test initialization without token raises ValueError."""
        with patch.dict('os.environ', {}, clear=True):
            with self.assertRaises(ValueError) as context:
                GitHubClient()
            self.assertIn("GitHub token is required", str(context.exception))

    @patch('utils.github_client.Github')
    def test_get_file_content_success(self, mock_github_class):
        """Test successful file content retrieval."""
        # Setup mocks
        mock_github = Mock()
        mock_github_class.return_value = mock_github

        mock_repo = Mock()
        mock_github.get_repo.return_value = mock_repo

        test_content = "Test file content"
        encoded_content = base64.b64encode(test_content.encode('utf-8')).decode('utf-8')
        mock_file_content = Mock()
        mock_file_content.content = encoded_content
        mock_repo.get_contents.return_value = mock_file_content

        # Test
        client = GitHubClient(token=self.test_token)
        result = client.get_file_content(self.test_owner, self.test_repo, self.test_file_path, self.test_ref)

        # Assertions
        self.assertEqual(result, test_content)
        mock_github.get_repo.assert_called_once_with(f"{self.test_owner}/{self.test_repo}")
        mock_repo.get_contents.assert_called_once_with(self.test_file_path, ref=self.test_ref)

    @patch('utils.github_client.Github')
    def test_get_file_content_empty_file(self, mock_github_class):
        """Test file content retrieval when file is empty."""
        # Setup mocks
        mock_github = Mock()
        mock_github_class.return_value = mock_github

        mock_repo = Mock()
        mock_github.get_repo.return_value = mock_repo

        mock_file_content = Mock()
        mock_file_content.content = None
        mock_repo.get_contents.return_value = mock_file_content

        # Test
        client = GitHubClient(token=self.test_token)
        result = client.get_file_content(self.test_owner, self.test_repo, self.test_file_path, self.test_ref)

        # Assertions
        self.assertIsNone(result)

    @patch('utils.github_client.Github')
    def test_get_file_content_404_error(self, mock_github_class):
        """Test file content retrieval with 404 error."""
        # Setup mocks
        mock_github = Mock()
        mock_github_class.return_value = mock_github

        mock_repo = Mock()
        mock_github.get_repo.return_value = mock_repo

        mock_repo.get_contents.side_effect = GithubException(404, {"message": "Not Found"})

        # Test
        client = GitHubClient(token=self.test_token)
        result = client.get_file_content(self.test_owner, self.test_repo, self.test_file_path, self.test_ref)

        # Assertions
        self.assertIsNone(result)

    @patch('utils.github_client.Github')
    def test_get_file_content_403_error(self, mock_github_class):
        """Test file content retrieval with 403 error."""
        # Setup mocks
        mock_github = Mock()
        mock_github_class.return_value = mock_github

        mock_repo = Mock()
        mock_github.get_repo.return_value = mock_repo

        mock_repo.get_contents.side_effect = GithubException(403, {"message": "Forbidden"})

        # Test
        client = GitHubClient(token=self.test_token)
        result = client.get_file_content(self.test_owner, self.test_repo, self.test_file_path, self.test_ref)

        # Assertions
        self.assertIsNone(result)

    @patch('utils.github_client.Github')
    def test_get_file_content_other_github_error(self, mock_github_class):
        """Test file content retrieval with other GitHub API error."""
        # Setup mocks
        mock_github = Mock()
        mock_github_class.return_value = mock_github

        mock_repo = Mock()
        mock_github.get_repo.return_value = mock_repo

        mock_repo.get_contents.side_effect = GithubException(500, {"message": "Internal Server Error"})

        # Test
        client = GitHubClient(token=self.test_token)
        result = client.get_file_content(self.test_owner, self.test_repo, self.test_file_path, self.test_ref)

        # Assertions
        self.assertIsNone(result)

    @patch('utils.github_client.Github')
    def test_get_file_content_general_exception(self, mock_github_class):
        """Test file content retrieval with general exception."""
        # Setup mocks
        mock_github = Mock()
        mock_github_class.return_value = mock_github

        mock_github.get_repo.side_effect = Exception("Network error")

        # Test
        client = GitHubClient(token=self.test_token)
        result = client.get_file_content(self.test_owner, self.test_repo, self.test_file_path, self.test_ref)

        # Assertions
        self.assertIsNone(result)

    @patch.object(GitHubClient, 'get_file_content')
    def test_get_sca_exceptions_success(self, mock_get_file_content):
        """Test successful SCA exceptions retrieval."""
        # Setup mock data
        fp_data = {"exceptions": [{"name": "dep1", "comment": "test"}]}
        fn_data = {"exceptions": [{"name": "dep2", "comment": "test"}]}

        mock_get_file_content.side_effect = [
            json.dumps(fp_data),  # First call for false positives
            json.dumps(fn_data)   # Second call for false negatives
        ]

        # Test
        client = GitHubClient(token=self.test_token)
        result = client.get_sca_exceptions(self.test_owner, self.test_repo, self.test_ref)

        # Assertions
        expected = {
            'false_positives': {'dep1'},
            'false_negatives': {'dep2'}
        }
        self.assertEqual(result, expected)
        self.assertEqual(mock_get_file_content.call_count, 2)

    @patch.object(GitHubClient, 'get_file_content')
    def test_get_sca_exceptions_no_files(self, mock_get_file_content):
        """Test SCA exceptions retrieval when no files exist."""
        mock_get_file_content.return_value = None

        # Test
        client = GitHubClient(token=self.test_token)
        result = client.get_sca_exceptions(self.test_owner, self.test_repo, self.test_ref)

        # Assertions
        expected = {
            'false_positives': set(),
            'false_negatives': set()
        }
        self.assertEqual(result, expected)

    def test_parse_exceptions_json_valid(self):
        """Test parsing valid JSON exceptions."""
        json_data = {
            "exceptions": [
                {"name": "dep1", "comment": "test comment 1"},
                {"name": "dep2", "comment": "test comment 2"}
            ]
        }
        content = json.dumps(json_data)

        client = GitHubClient(token=self.test_token)
        result = client._parse_exceptions_json(content)

        expected = {"dep1", "dep2"}
        self.assertEqual(result, expected)

    def test_parse_exceptions_json_invalid_json(self):
        """Test parsing invalid JSON."""
        content = "invalid json content"

        client = GitHubClient(token=self.test_token)
        result = client._parse_exceptions_json(content)

        self.assertEqual(result, set())

    @patch('utils.github_client.json.loads')
    def test_parse_exceptions_json_general_exception(self, mock_json_loads):
        """Test parsing JSON with general exception."""
        mock_json_loads.side_effect = Exception("Unexpected error")

        client = GitHubClient(token=self.test_token)
        result = client._parse_exceptions_json("some content")

        self.assertEqual(result, set())

    def test_parse_exceptions_json_wrong_format(self):
        """Test parsing JSON with wrong format."""
        json_data = {"wrong": "format"}
        content = json.dumps(json_data)

        client = GitHubClient(token=self.test_token)
        result = client._parse_exceptions_json(content)

        self.assertEqual(result, set())

    def test_parse_exceptions_json_invalid_exceptions_format(self):
        """Test parsing JSON with invalid exceptions format."""
        json_data = {"exceptions": "not a list"}
        content = json.dumps(json_data)

        client = GitHubClient(token=self.test_token)
        result = client._parse_exceptions_json(content)

        self.assertEqual(result, set())

    def test_parse_exceptions_json_invalid_item(self):
        """Test parsing JSON with invalid exception items."""
        json_data = {
            "exceptions": [
                {"name": "dep1", "comment": "valid"},
                "invalid item",
                {"wrong": "format"}
            ]
        }
        content = json.dumps(json_data)

        client = GitHubClient(token=self.test_token)
        result = client._parse_exceptions_json(content)

        expected = {"dep1"}
        self.assertEqual(result, expected)

    def test_extract_exceptions_from_data_valid(self):
        """Test extracting exceptions from valid data."""
        data = {
            "exceptions": [
                {"name": "dep1", "comment": "test comment 1"},
                {"name": "dep2", "comment": "test comment 2"}
            ]
        }

        client = GitHubClient(token=self.test_token)
        result = client._extract_exceptions_from_data(data)

        expected = {"dep1", "dep2"}
        self.assertEqual(result, expected)

    def test_extract_exceptions_from_data_invalid_format(self):
        """Test extracting exceptions from invalid data format."""
        data = {"wrong": "format"}

        client = GitHubClient(token=self.test_token)
        result = client._extract_exceptions_from_data(data)

        self.assertEqual(result, set())

    def test_extract_exceptions_from_data_invalid_exceptions(self):
        """Test extracting exceptions from data with invalid exceptions."""
        data = {"exceptions": "not a list"}

        client = GitHubClient(token=self.test_token)
        result = client._extract_exceptions_from_data(data)

        self.assertEqual(result, set())

    @patch('utils.github_client.Github')
    def test_test_connection_success(self, mock_github_class):
        """Test successful connection test."""
        # Setup mocks
        mock_github = Mock()
        mock_github_class.return_value = mock_github

        mock_repo = Mock()
        mock_repo.name = "test-repo"
        mock_github.get_repo.return_value = mock_repo

        # Test
        client = GitHubClient(token=self.test_token)
        result = client.test_connection(self.test_owner, self.test_repo)

        # Assertions
        self.assertTrue(result)
        mock_github.get_repo.assert_called_once_with(f"{self.test_owner}/{self.test_repo}")

    @patch('utils.github_client.Github')
    def test_test_connection_404_error(self, mock_github_class):
        """Test connection test with 404 error."""
        # Setup mocks
        mock_github = Mock()
        mock_github_class.return_value = mock_github

        mock_github.get_repo.side_effect = GithubException(404, {"message": "Not Found"})

        # Test
        client = GitHubClient(token=self.test_token)
        result = client.test_connection(self.test_owner, self.test_repo)

        # Assertions
        self.assertFalse(result)

    @patch('utils.github_client.Github')
    def test_test_connection_403_error(self, mock_github_class):
        """Test connection test with 403 error."""
        # Setup mocks
        mock_github = Mock()
        mock_github_class.return_value = mock_github

        mock_github.get_repo.side_effect = GithubException(403, {"message": "Forbidden"})

        # Test
        client = GitHubClient(token=self.test_token)
        result = client.test_connection(self.test_owner, self.test_repo)

        # Assertions
        self.assertFalse(result)

    @patch('utils.github_client.Github')
    def test_test_connection_other_github_error(self, mock_github_class):
        """Test connection test with other GitHub API error."""
        # Setup mocks
        mock_github = Mock()
        mock_github_class.return_value = mock_github

        mock_github.get_repo.side_effect = GithubException(500, {"message": "Internal Server Error"})

        # Test
        client = GitHubClient(token=self.test_token)
        result = client.test_connection(self.test_owner, self.test_repo)

        # Assertions
        self.assertFalse(result)

    @patch('utils.github_client.Github')
    def test_test_connection_general_exception(self, mock_github_class):
        """Test connection test with general exception."""
        # Setup mocks
        mock_github = Mock()
        mock_github_class.return_value = mock_github

        mock_github.get_repo.side_effect = Exception("Network error")

        # Test
        client = GitHubClient(token=self.test_token)
        result = client.test_connection(self.test_owner, self.test_repo)

        # Assertions
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
