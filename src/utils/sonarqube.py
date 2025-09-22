import json
import requests
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class SonarQube:
    """Utility class for interacting with SonarQube API."""

    def __init__(self, base_url: str, token: str):
        """
        Initialize SonarQube client.

        Args:
            base_url: SonarQube instance URL (e.g., https://next.sonarqube.com/)
            token: SonarQube authentication token
        """
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

    def download_sbom(self, component: str, branch: str = "master", sbom_type: str = "cyclonedx") -> Optional[Dict[str, Any]]:
        """
        Download SBOM (Software Bill of Materials) from SonarQube.

        Args:
            component: Component key (e.g., org.sonarsource.javascript:javascript)
            branch: Branch name (default: master)
            sbom_type: SBOM format type (default: cyclonedx)

        Returns:
            SBOM data as dictionary, or None if failed
        """
        try:
            url = f"{self.base_url}/sonarqube/api/v2/sca/sbom-reports"
            params = {
                'component': component,
                'type': sbom_type,
                'branch': branch
            }

            # Set appropriate Accept header based on SBOM type
            headers = self.headers.copy()
            if sbom_type == "cyclonedx":
                headers['Accept'] = 'application/vnd.cyclonedx+json'
            elif sbom_type == "spdx_23":
                headers['Accept'] = 'application/spdx+json'

            logger.info(f"Downloading SBOM from SonarQube: {url}")
            logger.info(f"Parameters: component={component}, branch={branch}, type={sbom_type}")
            logger.info(f"Accept header: {headers['Accept']}")

            response = requests.get(url, headers=headers, params=params, timeout=30)

            if response.status_code == 200:
                sbom_data = response.json()
                logger.info(f"Successfully downloaded SBOM for component: {component}")
                return sbom_data
            else:
                logger.error(f"Failed to download SBOM: {response.status_code} - {response.text}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed while downloading SBOM: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse SBOM JSON response: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error while downloading SBOM: {e}")
            return None

    def get_project_key_from_env(self) -> Optional[str]:
        """
        Get SonarQube project key from environment variable.

        Returns:
            The SonarQube project key from SONAR_PROJECT_KEY env var, or None if not set.
        """
        import os
        project_key = os.getenv('SONAR_PROJECT_KEY')
        if project_key:
            logger.info(f"Using SonarQube project key from environment: {project_key}")
            return project_key
        else:
            logger.warning("SONAR_PROJECT_KEY environment variable not set")
            return None
