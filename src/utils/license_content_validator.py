"""
License content validation utility.

This module provides functionality to validate license file content against
reference license files instead of relying on filename patterns.
"""

import os
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class LicenseContentValidator:
    """Validates license file content against reference license files."""

    # Allowed licenses at SonarSource
    ALLOWED_LICENSES = {
        'LGPL-2.1', 'LGPL-3.0', 'Apache-2.0', 'MIT', 'BSD-2-Clause', 'BSD-3-Clause',
        'EPL-1.0', 'EPL-2.0', 'PSF-2.0'
    }

    def __init__(self, reference_licenses_dir: str = "src/resources/reference-licenses"):
        """Initialize the validator with reference license directory."""
        self.reference_licenses_dir = Path(reference_licenses_dir)
        self._reference_licenses: Dict[str, str] = {}
        self._load_reference_licenses()

    def _load_reference_licenses(self) -> None:
        """Load reference license files into memory."""
        if not self.reference_licenses_dir.exists():
            logger.warning(f"Reference licenses directory not found: {self.reference_licenses_dir}")
            return

        for license_file in self.reference_licenses_dir.glob("*.txt"):
            license_name = license_file.stem
            try:
                with open(license_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                self._reference_licenses[license_name] = self._normalize_license_content(content)
                logger.debug(f"Loaded reference license: {license_name}")
            except Exception as e:
                logger.warning(f"Failed to load reference license {license_file}: {e}")

    def _normalize_license_content(self, content: str) -> str:
        """Normalize license content for comparison."""
        # Remove extra whitespace and normalize line endings
        content = re.sub(r'\s+', ' ', content.strip())
        # Remove common variable placeholders
        content = content.replace('[year]', 'YYYY')
        content = content.replace('[fullname]', 'AUTHOR')
        content = content.replace('[name of copyright owner]', 'AUTHOR')
        # Convert to lowercase for case-insensitive comparison
        return content.lower()

    def validate_license_content(self, license_content: str, expected_license: str) -> Tuple[bool, float, str]:
        """
        Validate license content against expected license type.

        Args:
            license_content: The content of the license file to validate
            expected_license: The expected license type (e.g., 'Apache-2.0', 'MIT')

        Returns:
            Tuple of (is_valid, similarity_score, matched_license)
        """
        if expected_license not in self.ALLOWED_LICENSES:
            return False, 0.0, f"Unknown license type: {expected_license}"

        normalized_content = self._normalize_license_content(license_content)

        # Try exact match first
        if expected_license in self._reference_licenses:
            reference_content = self._reference_licenses[expected_license]
            if normalized_content == reference_content:
                return True, 1.0, expected_license

        # Try fuzzy matching against all reference licenses
        best_match = None
        best_score = 0.0

        for license_name, reference_content in self._reference_licenses.items():
            similarity = SequenceMatcher(None, normalized_content, reference_content).ratio()
            if similarity > best_score:
                best_score = similarity
                best_match = license_name

        # Consider it a match if similarity is above 80%
        if best_score >= 0.8:
            return True, best_score, best_match

        return False, best_score, best_match or "No match found"

    def validate_license_file(self, file_path: str, expected_license: str) -> Tuple[bool, float, str]:
        """
        Validate a license file against expected license type.

        Args:
            file_path: Path to the license file
            expected_license: The expected license type

        Returns:
            Tuple of (is_valid, similarity_score, matched_license)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return self.validate_license_content(content, expected_license)
        except Exception as e:
            logger.error(f"Failed to read license file {file_path}: {e}")
            return False, 0.0, f"Error reading file: {e}"

    def get_available_licenses(self) -> Set[str]:
        """Get set of available reference licenses."""
        return set(self._reference_licenses.keys())

    def get_allowed_licenses(self) -> Set[str]:
        """Get set of allowed licenses at SonarSource."""
        return self.ALLOWED_LICENSES.copy()


class LicenseContentMatcher:
    """Matches license files to SBOM components based on content validation."""

    def __init__(self, validator: LicenseContentValidator):
        """Initialize with a license content validator."""
        self.validator = validator

    def match_licenses_to_components(self,
                                   extracted_licenses: Dict[str, List[Dict]],
                                   sbom_components: List[Dict]) -> Dict[str, Dict]:
        """
        Match extracted license files to SBOM components based on content validation.

        Args:
            extracted_licenses: Dictionary mapping artifact names to license files
            sbom_components: List of SBOM components with license information

        Returns:
            Dictionary with matching results and validation details
        """
        results = {
            'matched_licenses': [],
            'unmatched_licenses': [],
            'validation_errors': [],
            'coverage_percentage': 0.0
        }

        # Create a mapping of component names to their license information
        component_licenses = self._build_component_licenses_map(sbom_components)

        # Process each artifact's license files
        self._process_license_files(extracted_licenses, component_licenses, results)

        # Calculate coverage percentage
        total_components = len(component_licenses)
        matched_components = len({match['component_name'] for match in results['matched_licenses']})
        if total_components > 0:
            results['coverage_percentage'] = (matched_components / total_components) * 100

        return results

    def _build_component_licenses_map(self, sbom_components: List[Dict]) -> Dict[str, str]:
        """Build a mapping of component names to their license information."""
        component_licenses = {}
        for component in sbom_components:
            name = component.get('name', '')
            licenses = component.get('licenses', [])
            if licenses:
                license_type = self._extract_license_type(licenses)
                component_licenses[name] = license_type
        return component_licenses

    def _extract_license_type(self, licenses: List) -> str:
        """Extract license type from licenses list."""
        license_info = licenses[0] if isinstance(licenses, list) else licenses
        if isinstance(license_info, dict):
            return license_info.get('id', '') or license_info.get('expression', '')
        return str(license_info)

    def _process_license_files(self, extracted_licenses: Dict[str, List[Dict]],
                              component_licenses: Dict[str, str], results: Dict) -> None:
        """Process all license files and match them to components."""
        for artifact_name, license_files in extracted_licenses.items():
            for license_file in license_files:
                if license_file.get('type') != 'third_party':
                    continue
                self._process_single_license_file(artifact_name, license_file, component_licenses, results)

    def _process_single_license_file(self, artifact_name: str, license_file: Dict,
                                   component_licenses: Dict[str, str], results: Dict) -> None:
        """Process a single license file and attempt to match it."""
        license_name = license_file.get('name', '')
        license_content = license_file.get('content', '')

        dependency_name = self._extract_dependency_name_from_license_file(license_name)
        if not dependency_name:
            self._add_validation_error(results, artifact_name, license_name,
                                     'Could not extract dependency name from filename')
            return

        matched_component, expected_license = self._find_matching_component(
            dependency_name, component_licenses)

        if not matched_component:
            self._add_unmatched_license(results, artifact_name, license_name, dependency_name)
            return

        self._validate_and_record_license(artifact_name, license_name, dependency_name,
                                        matched_component, expected_license,
                                        license_content, results)

    def _find_matching_component(self, dependency_name: str,
                               component_licenses: Dict[str, str]) -> tuple:
        """Find matching SBOM component for dependency name."""
        for comp_name, comp_license in component_licenses.items():
            if self._names_match(dependency_name, comp_name):
                return comp_name, comp_license
        return None, None

    def _validate_and_record_license(self, artifact_name: str, license_name: str,
                                   dependency_name: str, matched_component: str,
                                   expected_license: str, license_content: str,
                                   results: Dict) -> None:
        """Validate license content and record the result."""
        is_valid, similarity, matched_license = self.validator.validate_license_content(
            license_content, expected_license)

        if is_valid:
            self._add_matched_license(results, artifact_name, license_name, dependency_name,
                                    matched_component, expected_license, matched_license, similarity)
        else:
            self._add_validation_error_with_details(results, artifact_name, license_name,
                                                  dependency_name, matched_component,
                                                  expected_license, matched_license, similarity)

    def _add_validation_error(self, results: Dict, artifact_name: str,
                            license_name: str, error: str) -> None:
        """Add a validation error to results."""
        results['validation_errors'].append({
            'artifact': artifact_name,
            'license_file': license_name,
            'error': error
        })

    def _add_unmatched_license(self, results: Dict, artifact_name: str,
                             license_name: str, dependency_name: str) -> None:
        """Add an unmatched license to results."""
        results['unmatched_licenses'].append({
            'artifact': artifact_name,
            'license_file': license_name,
            'dependency_name': dependency_name,
            'reason': 'No matching SBOM component found'
        })

    def _add_matched_license(self, results: Dict, artifact_name: str, license_name: str,
                           dependency_name: str, matched_component: str, expected_license: str,
                           matched_license: str, similarity: float) -> None:
        """Add a matched license to results."""
        results['matched_licenses'].append({
            'artifact': artifact_name,
            'license_file': license_name,
            'dependency_name': dependency_name,
            'component_name': matched_component,
            'expected_license': expected_license,
            'matched_license': matched_license,
            'similarity_score': similarity
        })

    def _add_validation_error_with_details(self, results: Dict, artifact_name: str,
                                         license_name: str, dependency_name: str,
                                         matched_component: str, expected_license: str,
                                         matched_license: str, similarity: float) -> None:
        """Add a validation error with detailed information to results."""
        results['validation_errors'].append({
            'artifact': artifact_name,
            'license_file': license_name,
            'dependency_name': dependency_name,
            'component_name': matched_component,
            'expected_license': expected_license,
            'matched_license': matched_license,
            'similarity_score': similarity,
            'error': 'License content does not match expected license'
        })

    def _extract_dependency_name_from_license_file(self, filename: str) -> Optional[str]:
        """Extract dependency name from license filename."""
        # Remove .txt extension
        name = filename.replace('.txt', '')
        # Remove -LICENSE suffix
        if name.endswith('-LICENSE'):
            return name[:-8]
        return None

    def _names_match(self, name1: str, name2: str) -> bool:
        """Check if two dependency names match (case-insensitive, normalized)."""
        # Normalize names for comparison
        norm1 = re.sub(r'[^a-zA-Z0-9]', '', name1.lower())
        norm2 = re.sub(r'[^a-zA-Z0-9]', '', name2.lower())
        return norm1 == norm2
