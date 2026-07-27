import os
from typing import Any, Optional
from urllib.parse import quote

import requests


class ArtifactoryClient:
    """Minimal Repox client for fetching build-info."""

    class FetchError(RuntimeError):
        """Raised when build-info cannot be fetched."""

        def __init__(self, message: str, status_code: Optional[int] = None):
            super().__init__(message)
            self.status_code = status_code

    def __init__(self, base_url: str, access_token: str, session: Optional[requests.Session] = None):
        self.base_url = base_url.rstrip('/')
        self.access_token = access_token
        self.session = session or requests.Session()

    @classmethod
    def from_env(cls) -> "ArtifactoryClient":
        base_url = os.getenv('ARTIFACTORY_URL')
        access_token = os.getenv('ARTIFACTORY_ACCESS_TOKEN')
        if not base_url or not access_token:
            raise ValueError(
                'ARTIFACTORY_URL and ARTIFACTORY_ACCESS_TOKEN must be set for CheckVersionConsistency'
            )
        return cls(base_url, access_token)

    def fetch_build_info(self, build_name: str, build_number: int | str) -> dict[str, Any]:
        # Align with gh-action_release Artifactory client (Bearer access token).
        encoded_name = quote(str(build_name), safe='')
        encoded_number = quote(str(build_number), safe='')
        url = f'{self.base_url}/api/build/{encoded_name}/{encoded_number}'
        response = self.session.get(
            url,
            headers={'Authorization': f'Bearer {self.access_token}'},
            timeout=30,
        )
        if response.status_code != 200:
            raise self.FetchError(
                f'Failed to fetch build-info for {build_name}:{build_number} '
                f'(HTTP {response.status_code})',
                status_code=response.status_code,
            )
        payload = response.json()
        build_info = payload.get('buildInfo')
        if not build_info:
            raise self.FetchError(f'No buildInfo in response for {build_name}:{build_number}')
        return build_info
