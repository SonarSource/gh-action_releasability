"""
GitHub API client for fetching repository-level SCA exceptions.

This module provides functionality to fetch false positive and false negative
files from a product repository using the GitHub API.
"""

import os
import json
import logging
import requests
from typing import Dict, Set, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class GitHubClient:
    """GitHub API client for fetching repository files."""

    def __init__(self, token: Optional[str] = None):
        """
        Initialize GitHub client.

        Args:
            token: GitHub personal access token. If None, will try to get from GH_TOKEN env var.
        """
        self.token = token or os.getenv('GH_TOKEN')
        if not self.token:
            raise ValueError("GitHub token is required. Set GH_TOKEN environment variable or pass token parameter.")

        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "sonarsource-gh-action-releasability"
        }

    def get_file_content(self, owner: str, repo: str, file_path: str, ref: str = "master") -> Optional[str]:
        """
        Get the content of a file from a GitHub repository.

        Args:
            owner: Repository owner (organization or user)
            repo: Repository name
            file_path: Path to the file in the repository
            ref: Git reference (branch, tag, or commit SHA). Defaults to "master"

        Returns:
            File content as string, or None if file doesn't exist or error occurs
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{file_path}"
        params = {"ref": ref}

        try:
            logger.info(f"Fetching file from GitHub: {owner}/{repo}/{file_path}@{ref}")
            response = requests.get(url, headers=self.headers, params=params, timeout=30)

            if response.status_code == 404:
                logger.debug(f"File not found: {owner}/{repo}/{file_path}")
                return None
            elif response.status_code == 403:
                logger.warning(f"Access forbidden for {owner}/{repo}/{file_path}. Check token permissions.")
                return None
            elif response.status_code != 200:
                logger.error(f"Failed to fetch file {owner}/{repo}/{file_path}: {response.status_code} - {response.text}")
                return None

            data = response.json()
            if 'content' not in data:
                logger.error(f"Unexpected response format for {owner}/{repo}/{file_path}")
                return None

            # Decode base64 content
            import base64
            content = base64.b64decode(data['content']).decode('utf-8')
            logger.info(f"Successfully fetched file {file_path} ({len(content)} characters)")
            return content

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching {owner}/{repo}/{file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching {owner}/{repo}/{file_path}: {e}")
            return None

    def get_sca_exceptions(self, owner: str, repo: str, ref: str = "master") -> Dict[str, Set[str]]:
        """
        Get SCA exceptions from a repository.

        Args:
            owner: Repository owner (organization or user)
            repo: Repository name
            ref: Git reference (branch, tag, or commit SHA). Defaults to "master"

        Returns:
            Dictionary with 'false_positives' and 'false_negatives' sets
        """
        exceptions = {
            'false_positives': set(),
            'false_negatives': set()
        }

        # Define the file paths in the repository
        fp_file_path = ".sca-exceptions/false-positives.json"
        fn_file_path = ".sca-exceptions/false-negatives.json"

        # Fetch false positives
        fp_content = self.get_file_content(owner, repo, fp_file_path, ref)
        if fp_content:
            fp_data = self._parse_exceptions_json(fp_content)
            exceptions['false_positives'] = fp_data
            logger.info(f"Loaded {len(fp_data)} false positives from {owner}/{repo}")

        # Fetch false negatives
        fn_content = self.get_file_content(owner, repo, fn_file_path, ref)
        if fn_content:
            fn_data = self._parse_exceptions_json(fn_content)
            exceptions['false_negatives'] = fn_data
            logger.info(f"Loaded {len(fn_data)} false negatives from {owner}/{repo}")

        return exceptions

    def _parse_exceptions_json(self, content: str) -> Set[str]:
        """
        Parse exceptions from JSON content.

        Args:
            content: JSON content as string

        Returns:
            Set of exception strings
        """
        try:
            data = json.loads(content)
            if isinstance(data, dict) and 'exceptions' in data:
                exceptions = data['exceptions']
                if isinstance(exceptions, list):
                    # New format: list of objects with name and comment
                    result = set()
                    for item in exceptions:
                        if isinstance(item, dict) and 'name' in item:
                            result.add(item['name'])
                        else:
                            logger.warning(f"Invalid exception item in JSON: {item}")
                    return result
                else:
                    logger.warning(f"Unexpected exceptions format in JSON")
                    return set()
            else:
                logger.warning(f"Unexpected JSON format. Expected object with 'exceptions' array.")
                return set()
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON content: {e}")
            return set()
        except Exception as e:
            logger.error(f"Unexpected error parsing JSON: {e}")
            return set()

    def test_connection(self, owner: str, repo: str) -> bool:
        """
        Test if the client can access the repository.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            True if connection is successful, False otherwise
        """
        url = f"{self.base_url}/repos/{owner}/{repo}"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                logger.info(f"Successfully connected to {owner}/{repo}")
                return True
            else:
                logger.warning(f"Cannot access {owner}/{repo}: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Connection test failed for {owner}/{repo}: {e}")
            return False
