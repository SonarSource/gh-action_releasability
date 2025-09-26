import json
import requests
import logging
import os
from typing import Optional, Dict, Any, Tuple

logger = logging.getLogger(__name__)


class SonarQube:
    """Utility class for interacting with SonarQube API."""

    # Instance configurations
    INSTANCES = {
        "next": {
            "url": "https://next.sonarqube.com",
            "api_url": "https://next.sonarqube.com/sonarqube/api/v2/sca/sbom-reports",
            "token_env": "SONARQUBE_TOKEN",
            "supports_sbom": True
        },
        "sonarcloud": {
            "url": "https://sonarcloud.io",
            "api_url": "https://api.sonarcloud.io/sca/sbom-reports",
            "token_env": "SONARCLOUD_TOKEN",
            "supports_sbom": True
        },
        "sonarqube.us": {
            "url": "https://sonarqube.us",
            "api_url": "https://sonarqube.us/sonarqube/api/v2/sca/sbom-reports",
            "token_env": "SONARQUBE_US_TOKEN",
            "supports_sbom": False
        }
    }

    def __init__(self, instance: str = None, base_url: str = None, token: str = None):
        """
        Initialize SonarQube client.

        Args:
            instance: SonarQube instance name (next, sonarcloud, sonarqube.us)
            base_url: SonarQube instance URL (overrides instance if provided)
            token: SonarQube authentication token (overrides instance if provided)
        """
        if instance and instance in self.INSTANCES:
            config = self.INSTANCES[instance]
            self.base_url = config["url"]
            self.api_url = config["api_url"]
            self.supports_sbom = config["supports_sbom"]

            # Get token from environment if not provided
            if not token:
                token = os.getenv(config["token_env"])
                if not token:
                    raise ValueError(f"Token not provided and {config['token_env']} environment variable not set")
        else:
            # Fallback to manual configuration
            if not base_url or not token:
                raise ValueError("Either instance name or both base_url and token must be provided")
            self.base_url = base_url.rstrip('/')
            self.api_url = f"{self.base_url}/sonarqube/api/v2/sca/sbom-reports"
            self.supports_sbom = True  # Assume supports SBOM for manual configuration

        self.token = token
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

    @classmethod
    def get_instance_config(cls, instance: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a SonarQube instance.

        Args:
            instance: Instance name (next, sonarcloud, sonarqube.us)

        Returns:
            Instance configuration dictionary or None if not found
        """
        return cls.INSTANCES.get(instance)

    @classmethod
    def get_available_instances(cls) -> list:
        """
        Get list of available SonarQube instances.

        Returns:
            List of instance names
        """
        return list(cls.INSTANCES.keys())

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
        # Check if this instance supports SBOM
        if not self.supports_sbom:
            logger.warning(f"SonarQube instance {self.base_url} does not support SBOM API")
            return None

        try:
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

            logger.info(f"Downloading SBOM from SonarQube: {self.api_url}")
            logger.info(f"Parameters: component={component}, branch={branch}, type={sbom_type}")
            logger.info(f"Accept header: {headers['Accept']}")

            response = requests.get(self.api_url, headers=headers, params=params, timeout=30)

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
