import os
from typing import Any, Optional

import requests


class ArtifactoryClient:
    """Minimal Repox client for fetching build-info."""

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
        url = f'{self.base_url}/api/build/{build_name}/{build_number}'
        response = self.session.get(
            url,
            headers={'X-JFrog-Art-Api': self.access_token},
            timeout=30,
        )
        if response.status_code != 200:
            raise RuntimeError(
                f'Failed to fetch build-info for {build_name}:{build_number} '
                f'(HTTP {response.status_code})'
            )
        payload = response.json()
        build_info = payload.get('buildInfo')
        if not build_info:
            raise RuntimeError(f'No buildInfo in response for {build_name}:{build_number}')
        return build_info
