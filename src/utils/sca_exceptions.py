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
from typing import Dict, List, Set, Optional, Union

logger = logging.getLogger(__name__)


class SCAExceptionManager:
    """Manages SCA False Positives and False Negatives exceptions."""

    def __init__(self, repository_root: str = "."):
        """
        Initialize SCA exception manager.

        Args:
            repository_root: Root directory of the repository
        """
        self.repository_root = Path(repository_root)
        self.fp_file = self.repository_root / ".sca-exceptions" / "false-positives.json"
        self.fn_file = self.repository_root / ".sca-exceptions" / "false-negatives.json"

        # Load exceptions
        self.false_positives = self._load_exceptions(self.fp_file)
        self.false_negatives = self._load_exceptions(self.fn_file)

        logger.info(f"Loaded {len(self.false_positives)} FPs and {len(self.false_negatives)} FNs")

    def _load_exceptions(self, file_path: Path) -> Set[str]:
        """Load exceptions from JSON file."""
        if not file_path.exists():
            logger.debug(f"Exception file not found: {file_path}")
            return set()

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return set(data)
                elif isinstance(data, dict) and 'exceptions' in data:
                    return set(data['exceptions'])
                else:
                    logger.warning(f"Unexpected format in {file_path}")
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
        license_extensions = ['.txt', '.html', '.htm', '.md']

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
        elif file.lower() in ['license.txt', 'license.html', 'license.htm', 'license.md']:
            return 'main'
        else:
            return 'third_party'  # Default to third-party

    @staticmethod
    def _determine_file_format(file_ext: str) -> str:
        """Determine the file format based on extension."""
        return 'html' if file_ext in ['.html', '.htm'] else 'text'

    @staticmethod
    def extract_dependency_name_from_license_file(file_name: str) -> str:
        """
        Extract dependency name from license file name.

        Supports various naming patterns:
        - LibraryA-LICENSE.txt
        - LibraryA_LICENSE.txt
        - LibraryA-LICENSE.html
        - LibraryA.txt
        - LibraryA.html
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

        return name.strip()


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

        # Apply FP/FN logic:
        # Expected = SCA + FNs - FPs
        # Actual = License files
        expected_dependencies = (sca_dependencies | fns) - fps
        actual_dependencies = license_dependencies

        # Calculate differences
        missing_dependencies = expected_dependencies - actual_dependencies
        extra_dependencies = actual_dependencies - expected_dependencies

        # Calculate coverage
        total_expected = len(expected_dependencies)
        coverage_percentage = 0.0
        if total_expected > 0:
            matched = len(expected_dependencies & actual_dependencies)
            coverage_percentage = (matched / total_expected) * 100

        return {
            'expected_dependencies': expected_dependencies,
            'actual_dependencies': actual_dependencies,
            'missing_dependencies': missing_dependencies,
            'extra_dependencies': extra_dependencies,
            'coverage_percentage': coverage_percentage,
            'false_positives_used': fps,
            'false_negatives_used': fns,
            'total_expected': total_expected,
            'total_actual': len(actual_dependencies),
            'matched_count': len(expected_dependencies & actual_dependencies)
        }

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
