"""
License Packaging Standard (LPS) utilities for license extraction and comparison.

This module implements the LPS specification for organizing and comparing
licenses in Sonar software distributions.
"""

import os
import zipfile
import tarfile
import tempfile
import logging
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
import json

from utils.sca_exceptions import SCAExceptionManager, LicenseFileDetector, SCAComparisonEngine

logger = logging.getLogger(__name__)


class LicenseExtractor:
    """Extracts license files from artifacts according to LPS specification."""

    def __init__(self):
        self.temp_dir = None

    def extract_licenses_from_artifacts(self, artifacts: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Extract license files from all artifacts.

        Args:
            artifacts: List of artifact dictionaries with 'path' and 'name' keys

        Returns:
            Dictionary mapping artifact names to their license information
        """
        results = {}

        for artifact in artifacts:
            artifact_path = artifact['path']
            artifact_name = artifact['name']

            logger.info(f"Extracting licenses from {artifact_name}")

            try:
                licenses = self._extract_licenses_from_artifact(artifact_path)
                results[artifact_name] = licenses
                logger.info(f"Found {len(licenses)} license files in {artifact_name}")
            except Exception as e:
                logger.error(f"Failed to extract licenses from {artifact_name}: {e}")
                results[artifact_name] = []

        return results

    def _extract_licenses_from_artifact(self, artifact_path: str) -> List[Dict]:
        """Extract license files from a single artifact."""
        licenses = []

        if not os.path.exists(artifact_path):
            logger.warning(f"Artifact file not found: {artifact_path}")
            return licenses

        # Create temporary directory for extraction
        self.temp_dir = tempfile.mkdtemp(prefix="license_extraction_")

        try:
            if artifact_path.endswith('.jar') or artifact_path.endswith('.zip'):
                licenses = self._extract_from_archive(artifact_path)
            else:
                logger.warning(f"Unsupported artifact format: {artifact_path}")

        except Exception as e:
            logger.error(f"Error extracting licenses from {artifact_path}: {e}")
        finally:
            # Clean up temporary directory
            if self.temp_dir and os.path.exists(self.temp_dir):
                import shutil
                shutil.rmtree(self.temp_dir, ignore_errors=True)

        return licenses

    def _extract_from_archive(self, archive_path: str) -> List[Dict]:
        """Extract license files from JAR/ZIP archive."""
        licenses = []

        with zipfile.ZipFile(archive_path, 'r') as archive:
            # Extract all files to temporary directory
            archive.extractall(self.temp_dir)

            # Look for licenses directory
            licenses_dir = os.path.join(self.temp_dir, 'licenses')
            if os.path.exists(licenses_dir):
                licenses.extend(self._extract_licenses_from_directory(licenses_dir, 'main'))

            # Look for inner archives and their licenses
            licenses.extend(self._extract_from_inner_archives())

        return licenses

    def _extract_from_inner_archives(self) -> List[Dict]:
        """Extract licenses from inner archives (e.g., .zip files inside JAR)."""
        licenses = []

        if not self.temp_dir:
            return licenses

        # Look for inner archives
        for root, dirs, files in os.walk(self.temp_dir):
            for file in files:
                if self._is_archive_file(file):
                    inner_archive_path = os.path.join(root, file)
                    logger.info(f"Found inner archive: {file}")

                    inner_licenses = self._process_inner_archive(inner_archive_path, file, root)
                    licenses.extend(inner_licenses)

        return licenses

    def _is_archive_file(self, filename: str) -> bool:
        """Check if file is a supported archive format."""
        return filename.endswith(('.zip', '.tgz', '.txz', '.xz'))

    def _process_inner_archive(self, archive_path: str, filename: str, root_dir: str) -> List[Dict]:
        """Process a single inner archive and extract licenses."""
        licenses = []
        inner_temp_dir = tempfile.mkdtemp(prefix="inner_archive_")

        try:
            if not self._extract_archive_to_temp(archive_path, filename, inner_temp_dir):
                return licenses

            # Extract licenses from inner archive
            licenses.extend(self._extract_licenses_from_inner_archive(inner_temp_dir, filename))

            # Extract licenses from dedicated license directory
            licenses.extend(self._extract_licenses_from_dedicated_dir(root_dir, filename))

        except Exception as e:
            logger.error(f"Error processing inner archive {filename}: {e}")
        finally:
            self._cleanup_temp_directory(inner_temp_dir)

        return licenses

    def _extract_archive_to_temp(self, archive_path: str, filename: str, temp_dir: str) -> bool:
        """Extract archive to temporary directory."""
        if filename.endswith('.zip'):
            with zipfile.ZipFile(archive_path, 'r') as inner_archive:
                inner_archive.extractall(temp_dir)
            return True
        elif filename.endswith('.tgz'):
            with tarfile.open(archive_path, 'r:gz') as inner_archive:
                inner_archive.extractall(temp_dir)
            return True
        else:
            logger.warning(f"Compressed file format not yet supported: {filename}")
            return False

    def _extract_licenses_from_inner_archive(self, temp_dir: str, filename: str) -> List[Dict]:
        """Extract licenses from inner archive's licenses directory."""
        inner_licenses_dir = os.path.join(temp_dir, 'licenses')
        if os.path.exists(inner_licenses_dir):
            return self._extract_licenses_from_directory(inner_licenses_dir, f'inner_{filename}')
        return []

    def _extract_licenses_from_dedicated_dir(self, root_dir: str, filename: str) -> List[Dict]:
        """Extract licenses from dedicated license directory alongside archive."""
        license_dir_name = f"{os.path.splitext(filename)[0]}-licenses"
        dedicated_license_dir = os.path.join(root_dir, license_dir_name)
        if os.path.exists(dedicated_license_dir):
            return self._extract_licenses_from_directory(dedicated_license_dir, f'dedicated_{filename}')
        return []

    def _cleanup_temp_directory(self, temp_dir: str) -> None:
        """Clean up temporary directory."""
        if os.path.exists(temp_dir):
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _extract_licenses_from_directory(self, licenses_dir: str, source: str) -> List[Dict]:
        """Extract license information from a licenses directory."""
        licenses = []

        # Use the enhanced license file detector
        license_files = LicenseFileDetector.detect_license_files(licenses_dir)

        for license_file in license_files:
            licenses.append({
                'type': license_file['type'],
                'source': source,
                'path': license_file['path'],
                'name': license_file['name'],
                'format': license_file['format'],
                'content': self._read_file_content(license_file['path'])
            })

        return licenses

    def _read_file_content(self, file_path: str) -> str:
        """Read file content safely."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return ""


class LicenseComparator:
    """Compares extracted licenses with SBOM components with FP/FN support."""

    def __init__(self, repository_root: str = "."):
        """
        Initialize license comparator with SCA exception support.

        Args:
            repository_root: Root directory of the repository
        """
        self.sbom_components = []
        self.exception_manager = SCAExceptionManager(repository_root)
        self.comparison_engine = SCAComparisonEngine(self.exception_manager)

    def load_sbom(self, sbom_data: Dict) -> None:
        """Load SBOM data for comparison."""
        self.sbom_components = sbom_data.get('components', [])
        logger.info(f"Loaded {len(self.sbom_components)} components from SBOM")

    def compare_licenses_with_sbom(self, extracted_licenses: Dict[str, List[Dict]]) -> Dict[str, any]:
        """
        Compare extracted licenses with SBOM components, accounting for FPs and FNs.

        Args:
            extracted_licenses: Dictionary mapping artifact names to license lists

        Returns:
            Comparison results dictionary
        """
        results = {
            'total_artifacts': len(extracted_licenses),
            'total_licenses_found': 0,
            'total_sbom_components': len(self.sbom_components),
            'missing_licenses': [],
            'extra_licenses': [],
            'matched_licenses': [],
            'coverage_percentage': 0.0,
            'false_positives_used': [],
            'false_negatives_used': [],
            'is_compliant': False
        }

        # Collect all third-party licenses
        all_third_party_licenses = []
        for artifact_name, licenses in extracted_licenses.items():
            for license_info in licenses:
                if license_info['type'] == 'third_party':
                    all_third_party_licenses.append(license_info)

        results['total_licenses_found'] = len(all_third_party_licenses)

        # Extract component and license names
        sbom_component_names = self._extract_component_names()
        license_names = self._extract_license_names(all_third_party_licenses)

        # Use enhanced comparison with FP/FN support
        comparison_result = self.comparison_engine.compare_with_exceptions(
            set(license_names),
            set(sbom_component_names)
        )

        # Update results with enhanced comparison
        results.update({
            'missing_licenses': list(comparison_result['missing_dependencies']),
            'extra_licenses': list(comparison_result['extra_dependencies']),
            'matched_licenses': list(comparison_result['expected_dependencies'] & comparison_result['actual_dependencies']),
            'coverage_percentage': comparison_result['coverage_percentage'],
            'false_positives_used': list(comparison_result['false_positives_used']),
            'false_negatives_used': list(comparison_result['false_negatives_used']),
            'is_compliant': self.comparison_engine.is_compliant(comparison_result)
        })

        return results

    def _extract_component_names(self) -> List[str]:
        """Extract component names from SBOM."""
        names = []
        for component in self.sbom_components:
            name = component.get('name', '')
            if name:
                names.append(name)
        return names

    def _extract_license_names(self, licenses: List[Dict]) -> List[str]:
        """Extract library names from license file names using enhanced detector."""
        names = []
        for license_info in licenses:
            # Use the enhanced license file detector
            clean_name = LicenseFileDetector.extract_dependency_name_from_license_file(license_info['name'])
            if clean_name and clean_name.lower() not in ['license', 'licenses']:
                names.append(clean_name)
        return names


class LPSValidator:
    """Validates compliance with License Packaging Standard."""

    def __init__(self, repository_root: str = "."):
        """
        Initialize LPS validator with SCA exception support.

        Args:
            repository_root: Root directory of the repository
        """
        self.extractor = LicenseExtractor()
        self.comparator = LicenseComparator(repository_root)

    def validate_artifacts(self, artifacts: List[Dict], sbom_data: Optional[Dict] = None) -> Dict[str, any]:
        """
        Validate artifacts against LPS specification.

        Args:
            artifacts: List of artifact dictionaries
            sbom_data: Optional SBOM data for comparison

        Returns:
            Validation results dictionary
        """
        results = {
            'lps_compliant': True,
            'artifacts_processed': 0,
            'licenses_extracted': {},
            'sbom_comparison': None,
            'issues': []
        }

        try:
            # Extract licenses from all artifacts
            extracted_licenses = self.extractor.extract_licenses_from_artifacts(artifacts)
            results['licenses_extracted'] = extracted_licenses
            results['artifacts_processed'] = len(extracted_licenses)

            # Check for LPS compliance issues
            issues = self._check_lps_compliance(extracted_licenses)
            results['issues'] = issues

            # Compare with SBOM if available
            if sbom_data:
                self.comparator.load_sbom(sbom_data)
                comparison = self.comparator.compare_licenses_with_sbom(extracted_licenses)
                results['sbom_comparison'] = comparison

                # Add SBOM-related issues
                if comparison['missing_licenses']:
                    results['issues'].append(f"Missing licenses for {len(comparison['missing_licenses'])} SBOM components")

                if comparison['coverage_percentage'] < 80:
                    results['issues'].append(f"Low license coverage: {comparison['coverage_percentage']:.1f}%")

            # Set compliance flag based on all issues
            if results['issues']:
                results['lps_compliant'] = False

        except Exception as e:
            logger.error(f"Error during LPS validation: {e}")
            results['lps_compliant'] = False
            results['issues'].append(f"Validation error: {str(e)}")

        return results

    def _check_lps_compliance(self, extracted_licenses: Dict[str, List[Dict]]) -> List[str]:
        """Check for LPS compliance issues."""
        issues = []

        for artifact_name, licenses in extracted_licenses.items():
            # Check for main LICENSE.txt
            main_licenses = [l for l in licenses if l['type'] == 'main']
            if not main_licenses:
                issues.append(f"Missing main LICENSE.txt in {artifact_name}")

            # Check for third-party licenses directory
            third_party_licenses = [l for l in licenses if l['type'] == 'third_party']
            if not third_party_licenses:
                issues.append(f"No third-party licenses found in {artifact_name}")

            # Check for proper directory structure
            has_licenses_dir = any('licenses' in l['path'] for l in licenses)
            if not has_licenses_dir:
                issues.append(f"No licenses/ directory found in {artifact_name}")

        return issues
