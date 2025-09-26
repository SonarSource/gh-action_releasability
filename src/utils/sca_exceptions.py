"""
SCA Exception Management for False Positives and False Negatives.

This module handles the configuration and management of SCA exceptions
to help improve SCA tool accuracy through dogfooding.
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Optional, Union, Tuple

from src.utils.github_client import GitHubClient

logger = logging.getLogger(__name__)


class SCAExceptionManager:
    """Manages SCA False Positives and False Negatives exceptions."""

    def __init__(self, repository_root: str = ".", github_owner: Optional[str] = None,
                 github_repo: Optional[str] = None, github_ref: str = "master"):
        """
        Initialize SCA exception manager.

        Args:
            repository_root: Root directory of the repository
            github_owner: GitHub organization/owner name for fetching repository-level exceptions
            github_repo: GitHub repository name for fetching repository-level exceptions
            github_ref: Git reference (branch, tag, or commit SHA) for fetching repository-level exceptions
        """
        self.repository_root = Path(repository_root)
        self.fp_file = self.repository_root / ".sca-exceptions" / "false-positives.json"
        self.fn_file = self.repository_root / ".sca-exceptions" / "false-negatives.json"

        # GitHub repository information
        self.github_owner = github_owner
        self.github_repo = github_repo
        self.github_ref = github_ref

        # Load exceptions from local files
        local_fps = self._load_exceptions(self.fp_file)
        local_fns = self._load_exceptions(self.fn_file)

        # Load exceptions from GitHub repository if specified
        github_fps = set()
        github_fns = set()
        if github_owner and github_repo:
            try:
                github_client = GitHubClient()
                github_exceptions = github_client.get_sca_exceptions(github_owner, github_repo, github_ref)
                github_fps = github_exceptions['false_positives']
                github_fns = github_exceptions['false_negatives']
                logger.info(f"Loaded {len(github_fps)} FPs and {len(github_fns)} FNs from {github_owner}/{github_repo}")
            except Exception as e:
                logger.warning(f"Failed to load exceptions from GitHub repository {github_owner}/{github_repo}: {e}")

        # Combine local and GitHub exceptions
        self.false_positives = local_fps | github_fps
        self.false_negatives = local_fns | github_fns

        logger.info(f"Total loaded: {len(self.false_positives)} FPs and {len(self.false_negatives)} FNs")
        if github_owner and github_repo:
            logger.info(f"  - Local: {len(local_fps)} FPs, {len(local_fns)} FNs")
            logger.info(f"  - GitHub: {len(github_fps)} FPs, {len(github_fns)} FNs")

    def _load_exceptions(self, file_path: Path) -> Set[str]:
        """Load exceptions from JSON file."""
        if not file_path.exists():
            logger.debug(f"Exception file not found: {file_path}")
            return set()

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict) and 'exceptions' in data:
                    exceptions = data['exceptions']
                    if isinstance(exceptions, list):
                        # New format: list of objects with name and comment
                        result = set()
                        for item in exceptions:
                            if isinstance(item, dict) and 'name' in item:
                                result.add(item['name'])
                            else:
                                logger.warning(f"Invalid exception item in {file_path}: {item}")
                        return result
                    else:
                        logger.warning(f"Unexpected exceptions format in {file_path}")
                        return set()
                else:
                    logger.warning(f"Unexpected format in {file_path}. Expected object with 'exceptions' array.")
                    return set()
        except Exception as e:
            logger.error(f"Error loading exceptions from {file_path}: {e}")
            return set()

    def get_false_positives(self) -> Set[str]:
        """Get the set of false positive dependencies."""
        return self.false_positives.copy()

    def get_false_negatives(self) -> Set[str]:
        """Get the set of false negative dependencies."""
        return self.false_negatives.copy()

    def get_detailed_false_positives(self) -> List[Dict[str, str]]:
        """Get detailed false positive information including comments."""
        return self._load_detailed_exceptions(self.fp_file)

    def get_detailed_false_negatives(self) -> List[Dict[str, str]]:
        """Get detailed false negative information including comments."""
        return self._load_detailed_exceptions(self.fn_file)

    def _load_detailed_exceptions(self, file_path: Path) -> List[Dict[str, str]]:
        """Load detailed exception information from JSON file."""
        if not file_path.exists():
            logger.debug(f"Exception file not found: {file_path}")
            return []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict) and 'exceptions' in data:
                    exceptions = data['exceptions']
                    if isinstance(exceptions, list):
                        # New format: list of objects with name and comment
                        result = []
                        for item in exceptions:
                            if isinstance(item, dict) and 'name' in item:
                                result.append({
                                    "name": item.get('name', ''),
                                    "comment": item.get('comment', '')
                                })
                            else:
                                logger.warning(f"Invalid exception item in {file_path}: {item}")
                        return result
                    else:
                        logger.warning(f"Unexpected exceptions format in {file_path}")
                        return []
                else:
                    logger.warning(f"Unexpected format in {file_path}. Expected object with 'exceptions' array.")
                    return []
        except Exception as e:
            logger.error(f"Error loading detailed exceptions from {file_path}: {e}")
            return []

    def is_false_positive(self, dependency: str) -> bool:
        """Check if a dependency is a known false positive."""
        return dependency in self.false_positives

    def is_false_negative(self, dependency: str) -> bool:
        """Check if a dependency is a known false negative."""
        return dependency in self.false_negatives

    def add_false_positive(self, dependency: str) -> None:
        """Add a dependency to the false positives list."""
        self.false_positives.add(dependency)
        self._save_exceptions(self.fp_file, self.false_positives)

    def add_false_negative(self, dependency: str) -> None:
        """Add a dependency to the false negatives list."""
        self.false_negatives.add(dependency)
        self._save_exceptions(self.fn_file, self.false_negatives)

    def _save_exceptions(self, file_path: Path, exceptions: Set[str]) -> None:
        """Save exceptions to JSON file."""
        try:
            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Save as sorted list for consistency
            data = {
                "exceptions": sorted(exceptions),
                "description": "SCA exceptions for this repository",
                "last_updated": datetime.now().isoformat()
            }

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved {len(exceptions)} exceptions to {file_path}")
        except Exception as e:
            logger.error(f"Error saving exceptions to {file_path}: {e}")

    def create_template_files(self) -> None:
        """Create template exception files if they don't exist."""
        if not self.fp_file.exists():
            self._save_exceptions(self.fp_file, set())
            logger.info(f"Created template FP file: {self.fp_file}")

        if not self.fn_file.exists():
            self._save_exceptions(self.fn_file, set())
            logger.info(f"Created template FN file: {self.fn_file}")


class LicenseFileDetector:
    """Enhanced license file detection supporting HTML and TXT formats."""

    @staticmethod
    def detect_license_files(licenses_dir: str) -> List[Dict[str, str]]:
        """
        Detect license files in a directory, supporting both TXT and HTML formats.

        Args:
            licenses_dir: Path to the licenses directory

        Returns:
            List of license file information dictionaries
        """
        license_files = []

        if not os.path.exists(licenses_dir):
            return license_files

        # Supported license file extensions
        license_extensions = ['.txt']

        for root, dirs, files in os.walk(licenses_dir):
            for file in files:
                file_path = os.path.join(root, file)
                file_ext = os.path.splitext(file)[1].lower()

                if file_ext in license_extensions:
                    license_info = LicenseFileDetector._create_license_info(file_path, file, file_ext)
                    license_files.append(license_info)

        return license_files

    @staticmethod
    def _create_license_info(file_path: str, file: str, file_ext: str) -> Dict[str, str]:
        """Create license file information dictionary."""
        license_type = LicenseFileDetector._determine_license_type(file_path, file)
        file_format = LicenseFileDetector._determine_file_format(file_ext)

        return {
            'path': file_path,
            'name': file,
            'type': license_type,
            'format': file_format
        }

    @staticmethod
    def _determine_license_type(file_path: str, file: str) -> str:
        """Determine if the file is a main license or third-party license."""
        if 'THIRD_PARTY_LICENSES' in file_path:
            return 'third_party'
        elif file.lower() == 'license.txt':
            return 'main'
        else:
            return 'third_party'  # Default to third-party

    @staticmethod
    def _determine_file_format(file_ext: str) -> str:
        """Determine the file format based on extension."""
        return 'text'

    @staticmethod
    def extract_dependency_name_from_license_file(file_name: str) -> str:
        """
        Extract dependency name from license file name.

        Supports various naming patterns:
        - LibraryA-LICENSE.txt
        - LibraryA_LICENSE.txt
        - LibraryA.txt
        - commons-io.commons-io_apache_v2.txt (Maven artifacts with version info)
        """
        # Remove common license suffixes
        name = file_name

        # Remove file extensions
        name = os.path.splitext(name)[0]

        # Remove common license suffixes
        license_suffixes = [
            '-LICENSE', '_LICENSE', '-license', '_license',
            '-License', '_License', '-License.txt', '_License.txt',
            '-LICENSE.txt', '_LICENSE.txt', '-license.txt', '_license.txt'
        ]

        for suffix in license_suffixes:
            if name.endswith(suffix):
                name = name[:-len(suffix)]
                break

        # Remove version-related suffixes (e.g., _apache_v2, _v2, etc.)
        import re
        # Pattern to match version suffixes like _apache_v2, _v1, _2.0, etc.
        version_pattern = r'(_apache_v\d+|_v\d+|_\d+\.\d+.*)$'
        name = re.sub(version_pattern, '', name)

        return name.strip()

    @staticmethod
    def normalize_maven_coordinate(component_name: str) -> str:
        """
        Normalize Maven coordinate format for comparison.

        Converts 'groupId:artifactId' to 'groupId.artifactId' format
        to match license file naming conventions.

        Args:
            component_name: Maven coordinate in format 'groupId:artifactId'

        Returns:
            Normalized name in format 'groupId.artifactId'
        """
        if ':' in component_name:
            # Convert Maven coordinate format (groupId:artifactId) to dot format
            return component_name.replace(':', '.')
        return component_name

    @staticmethod
    def normalize_for_comparison(name: str) -> str:
        """
        Normalize a name for comparison by applying all normalization rules.

        Args:
            name: Component name or license file name

        Returns:
            Normalized name ready for comparison
        """
        # First normalize Maven coordinates
        normalized = LicenseFileDetector.normalize_maven_coordinate(name)

        # Convert to lowercase for case-insensitive comparison
        normalized = normalized.lower().strip()

        # Handle cases where license files only contain artifact ID
        # For Maven coordinates like "com.google.code.gson:gson",
        # also try matching against just the artifact ID "gson"
        if ':' in name and '.' in normalized:
            # Extract artifact ID from Maven coordinate
            artifact_id = name.split(':')[-1].lower()
            # Add the artifact ID as an alternative for matching
            # We'll return the full coordinate but also consider artifact-only matches
            return normalized

        return normalized


class SCAComparisonEngine:
    """Enhanced SCA comparison engine with FP/FN support."""

    def __init__(self, exception_manager: SCAExceptionManager):
        """
        Initialize SCA comparison engine.

        Args:
            exception_manager: SCA exception manager instance
        """
        self.exception_manager = exception_manager

    def compare_with_exceptions(self,
                              license_dependencies: Set[str],
                              sca_dependencies: Set[str]) -> Dict[str, any]:
        """
        Compare license dependencies with SCA dependencies, accounting for FPs and FNs.

        Args:
            license_dependencies: Dependencies found in license files
            sca_dependencies: Dependencies reported by SCA

        Returns:
            Comparison results dictionary
        """
        # Get exceptions
        fps = self.exception_manager.get_false_positives()
        fns = self.exception_manager.get_false_negatives()

        # Normalize all dependency names for comparison
        normalized_license_deps = {LicenseFileDetector.normalize_for_comparison(name) for name in license_dependencies}
        normalized_sca_deps = {LicenseFileDetector.normalize_for_comparison(name) for name in sca_dependencies}
        normalized_fps = {LicenseFileDetector.normalize_for_comparison(name) for name in fps}
        normalized_fns = {LicenseFileDetector.normalize_for_comparison(name) for name in fns}

        # Apply fuzzy matching for Maven coordinates
        matched_pairs = self._find_fuzzy_matches(normalized_sca_deps, normalized_license_deps)

        # Create sets of matched dependencies
        matched_sca_deps = {pair[0] for pair in matched_pairs}
        matched_license_deps = {pair[1] for pair in matched_pairs}

        # Apply FP/FN logic:
        # Expected = SCA + FNs - FPs
        # Actual = License files
        expected_dependencies = (normalized_sca_deps | normalized_fns) - normalized_fps
        actual_dependencies = normalized_license_deps

        # Calculate differences using fuzzy matching
        # Missing: expected dependencies that are not found in license files
        # False negatives are considered as "found" if they exist in license dependencies
        found_dependencies = matched_license_deps | (normalized_fns & actual_dependencies)
        missing_dependencies = expected_dependencies - found_dependencies
        # Extra: license dependencies that are not expected (not in SCA + not false negatives)
        extra_dependencies = actual_dependencies - found_dependencies

        # Calculate coverage
        total_expected = len(expected_dependencies)
        coverage_percentage = 0.0
        if total_expected > 0:
            matched = len(found_dependencies & expected_dependencies)
            coverage_percentage = (matched / total_expected) * 100

        return {
            'expected_dependencies': expected_dependencies,
            'actual_dependencies': actual_dependencies,
            'missing_dependencies': missing_dependencies,
            'extra_dependencies': extra_dependencies,
            'coverage_percentage': coverage_percentage,
            'false_positives_used': normalized_fps,
            'false_negatives_used': normalized_fns,
            'total_expected': total_expected,
            'total_actual': len(actual_dependencies),
            'matched_count': len(matched_sca_deps & expected_dependencies),
            'fuzzy_matches': matched_pairs
        }

    def _find_fuzzy_matches(self, sca_deps: Set[str], license_deps: Set[str]) -> List[Tuple[str, str]]:
        """
        Find fuzzy matches between SCA dependencies and license dependencies.

        Handles cases like:
        - Full Maven coordinates vs artifact-only names
        - Different naming conventions

        Args:
            sca_deps: Set of normalized SCA dependency names
            license_deps: Set of normalized license dependency names

        Returns:
            List of (sca_dep, license_dep) matched pairs
        """
        matches = []
        used_license_deps = set()

        for sca_dep in sca_deps:
            # Try exact match first
            if sca_dep in license_deps and sca_dep not in used_license_deps:
                matches.append((sca_dep, sca_dep))
                used_license_deps.add(sca_dep)
                continue

            # Try fuzzy matching for Maven coordinates
            if '.' in sca_dep:
                # Extract artifact ID (last part after dots)
                artifact_id = sca_dep.split('.')[-1]

                # Look for license deps that match the artifact ID
                for license_dep in license_deps:
                    if license_dep not in used_license_deps:
                        # Check if license dep matches artifact ID or contains it
                        if (license_dep == artifact_id or
                            license_dep.endswith('.' + artifact_id) or
                            license_dep.startswith(artifact_id + '.') or
                            '.' + artifact_id + '.' in license_dep or
                            # Handle cases like "gson-gson" matching "gson"
                            (license_dep.count('-') > 0 and
                             any(part == artifact_id for part in license_dep.split('-')))):
                            matches.append((sca_dep, license_dep))
                            used_license_deps.add(license_dep)
                            break

        return matches

    def is_compliant(self, comparison_result: Dict[str, any]) -> bool:
        """
        Check if the repository is compliant based on comparison results.

        Compliant if and only if:
        - No missing dependencies
        - No extra dependencies
        - Coverage is 100%
        """
        return (len(comparison_result['missing_dependencies']) == 0 and
                len(comparison_result['extra_dependencies']) == 0 and
                comparison_result['coverage_percentage'] == 100)
