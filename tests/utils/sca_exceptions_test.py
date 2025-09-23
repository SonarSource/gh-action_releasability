"""
Unit tests for sca_exceptions.py module.
"""

import unittest
import tempfile
import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Adjust path for local imports
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from utils.sca_exceptions import SCAExceptionManager, LicenseFileDetector, SCAComparisonEngine


class TestSCAExceptionManager(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.manager = SCAExceptionManager(self.temp_dir)

    def tearDown(self):
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_init_creates_directories(self):
        """Test that initialization creates necessary directories."""
        # The directories are created when files are saved, not during init
        self.manager.create_template_files()
        self.assertTrue(self.manager.fp_file.parent.exists())
        self.assertTrue(self.manager.fn_file.parent.exists())

    def test_load_exceptions_empty_file(self):
        """Test loading exceptions from non-existent file."""
        exceptions = self.manager._load_exceptions(Path("/nonexistent/file.json"))
        self.assertEqual(exceptions, set())

    def test_load_exceptions_list_format(self):
        """Test loading exceptions from list format."""
        test_file = Path(self.temp_dir) / "test.json"
        with open(test_file, 'w') as f:
            json.dump(["dep1", "dep2", "dep3"], f)

        exceptions = self.manager._load_exceptions(test_file)
        self.assertEqual(exceptions, {"dep1", "dep2", "dep3"})

    def test_load_exceptions_dict_format(self):
        """Test loading exceptions from dict format."""
        test_file = Path(self.temp_dir) / "test.json"
        with open(test_file, 'w') as f:
            json.dump({"exceptions": ["dep1", "dep2"]}, f)

        exceptions = self.manager._load_exceptions(test_file)
        self.assertEqual(exceptions, {"dep1", "dep2"})

    def test_add_false_positive(self):
        """Test adding false positive."""
        self.manager.add_false_positive("test-dep")
        self.assertIn("test-dep", self.manager.get_false_positives())

    def test_add_false_negative(self):
        """Test adding false negative."""
        self.manager.add_false_negative("test-dep")
        self.assertIn("test-dep", self.manager.get_false_negatives())

    def test_is_false_positive(self):
        """Test checking if dependency is false positive."""
        self.manager.add_false_positive("test-dep")
        self.assertTrue(self.manager.is_false_positive("test-dep"))
        self.assertFalse(self.manager.is_false_positive("other-dep"))

    def test_is_false_negative(self):
        """Test checking if dependency is false negative."""
        self.manager.add_false_negative("test-dep")
        self.assertTrue(self.manager.is_false_negative("test-dep"))
        self.assertFalse(self.manager.is_false_negative("other-dep"))

    def test_create_template_files(self):
        """Test creating template files."""
        # Remove existing files
        if self.manager.fp_file.exists():
            self.manager.fp_file.unlink()
        if self.manager.fn_file.exists():
            self.manager.fn_file.unlink()

        self.manager.create_template_files()

        self.assertTrue(self.manager.fp_file.exists())
        self.assertTrue(self.manager.fn_file.exists())


class TestLicenseFileDetector(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_detect_license_files_empty_directory(self):
        """Test detection in empty directory."""
        licenses = LicenseFileDetector.detect_license_files(self.temp_dir)
        self.assertEqual(licenses, [])

    def test_detect_license_files_txt_format(self):
        """Test detection of TXT license files."""
        # Create test structure
        licenses_dir = os.path.join(self.temp_dir, "licenses")
        os.makedirs(licenses_dir)

        # Main license
        with open(os.path.join(licenses_dir, "LICENSE.txt"), 'w') as f:
            f.write("Main license")

        # Third-party licenses
        third_party_dir = os.path.join(licenses_dir, "THIRD_PARTY_LICENSES")
        os.makedirs(third_party_dir)

        with open(os.path.join(third_party_dir, "LibraryA-LICENSE.txt"), 'w') as f:
            f.write("Library A license")

        with open(os.path.join(third_party_dir, "LibraryB.txt"), 'w') as f:
            f.write("Library B license")

        licenses = LicenseFileDetector.detect_license_files(licenses_dir)

        self.assertEqual(len(licenses), 3)

        # Check main license
        main_licenses = [l for l in licenses if l['type'] == 'main']
        self.assertEqual(len(main_licenses), 1)
        self.assertEqual(main_licenses[0]['name'], 'LICENSE.txt')
        self.assertEqual(main_licenses[0]['format'], 'text')

        # Check third-party licenses
        third_party_licenses = [l for l in licenses if l['type'] == 'third_party']
        self.assertEqual(len(third_party_licenses), 2)

    def test_detect_license_files_html_format(self):
        """Test detection of HTML license files."""
        # Create test structure
        licenses_dir = os.path.join(self.temp_dir, "licenses")
        os.makedirs(licenses_dir)

        # Main license in HTML
        with open(os.path.join(licenses_dir, "LICENSE.html"), 'w') as f:
            f.write("<html><body>Main license</body></html>")

        # Third-party licenses in HTML
        third_party_dir = os.path.join(licenses_dir, "THIRD_PARTY_LICENSES")
        os.makedirs(third_party_dir)

        with open(os.path.join(third_party_dir, "LibraryA-LICENSE.html"), 'w') as f:
            f.write("<html><body>Library A license</body></html>")

        with open(os.path.join(third_party_dir, "LibraryB.htm"), 'w') as f:
            f.write("<html><body>Library B license</body></html>")

        licenses = LicenseFileDetector.detect_license_files(licenses_dir)

        self.assertEqual(len(licenses), 3)

        # Check HTML format detection
        html_licenses = [l for l in licenses if l['format'] == 'html']
        self.assertEqual(len(html_licenses), 3)

    def test_extract_dependency_name_from_license_file(self):
        """Test extracting dependency names from license file names."""
        test_cases = [
            ("LibraryA-LICENSE.txt", "LibraryA"),
            ("LibraryA_LICENSE.txt", "LibraryA"),
            ("LibraryA-LICENSE.html", "LibraryA"),
            ("LibraryA.txt", "LibraryA"),
            ("LibraryA.html", "LibraryA"),
            ("LibraryA-License.txt", "LibraryA"),
            ("LibraryA_license.txt", "LibraryA"),
            ("LICENSE.txt", "LICENSE"),
            ("license.txt", "license"),
        ]

        for filename, expected in test_cases:
            with self.subTest(filename=filename):
                result = LicenseFileDetector.extract_dependency_name_from_license_file(filename)
                self.assertEqual(result, expected)


class TestSCAComparisonEngine(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.manager = SCAExceptionManager(self.temp_dir)
        self.engine = SCAComparisonEngine(self.manager)

    def tearDown(self):
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_compare_with_exceptions_no_exceptions(self):
        """Test comparison without any exceptions."""
        license_deps = {"dep1", "dep2"}
        sca_deps = {"dep1", "dep3"}

        result = self.engine.compare_with_exceptions(license_deps, sca_deps)

        self.assertEqual(result['expected_dependencies'], sca_deps)
        self.assertEqual(result['actual_dependencies'], license_deps)
        self.assertEqual(result['missing_dependencies'], {"dep3"})
        self.assertEqual(result['extra_dependencies'], {"dep2"})
        self.assertEqual(result['coverage_percentage'], 50.0)

    def test_compare_with_exceptions_with_fps(self):
        """Test comparison with false positives."""
        # Add false positive
        self.manager.add_false_positive("dep3")

        license_deps = {"dep1", "dep2"}
        sca_deps = {"dep1", "dep3"}

        result = self.engine.compare_with_exceptions(license_deps, sca_deps)

        # dep3 should be excluded from expected due to FP
        self.assertEqual(result['expected_dependencies'], {"dep1"})
        self.assertEqual(result['missing_dependencies'], set())
        self.assertEqual(result['extra_dependencies'], {"dep2"})
        self.assertEqual(result['coverage_percentage'], 100.0)

    def test_compare_with_exceptions_with_fns(self):
        """Test comparison with false negatives."""
        # Add false negative
        self.manager.add_false_negative("dep2")

        license_deps = {"dep1", "dep2"}
        sca_deps = {"dep1"}

        result = self.engine.compare_with_exceptions(license_deps, sca_deps)

        # dep2 should be added to expected due to FN
        self.assertEqual(result['expected_dependencies'], {"dep1", "dep2"})
        self.assertEqual(result['missing_dependencies'], set())
        self.assertEqual(result['extra_dependencies'], set())
        self.assertEqual(result['coverage_percentage'], 100.0)

    def test_compare_with_exceptions_with_fps_and_fns(self):
        """Test comparison with both false positives and false negatives."""
        # Add exceptions
        self.manager.add_false_positive("dep3")  # SCA reports dep3 but it's FP
        self.manager.add_false_negative("dep4")  # License has dep4 but SCA doesn't report it

        license_deps = {"dep1", "dep2", "dep4"}
        sca_deps = {"dep1", "dep3"}

        result = self.engine.compare_with_exceptions(license_deps, sca_deps)

        # Expected = SCA + FNs - FPs = {dep1, dep3} + {dep4} - {dep3} = {dep1, dep4}
        self.assertEqual(result['expected_dependencies'], {"dep1", "dep4"})
        self.assertEqual(result['missing_dependencies'], set())
        self.assertEqual(result['extra_dependencies'], {"dep2"})
        self.assertEqual(result['coverage_percentage'], 100.0)

    def test_is_compliant_perfect_match(self):
        """Test compliance check with perfect match."""
        result = {
            'missing_dependencies': set(),
            'extra_dependencies': set(),
            'coverage_percentage': 100.0
        }

        self.assertTrue(self.engine.is_compliant(result))

    def test_is_compliant_missing_dependencies(self):
        """Test compliance check with missing dependencies."""
        result = {
            'missing_dependencies': {"dep1"},
            'extra_dependencies': set(),
            'coverage_percentage': 50.0
        }

        self.assertFalse(self.engine.is_compliant(result))

    def test_is_compliant_extra_dependencies(self):
        """Test compliance check with extra dependencies."""
        result = {
            'missing_dependencies': set(),
            'extra_dependencies': {"dep1"},
            'coverage_percentage': 50.0
        }

        self.assertFalse(self.engine.is_compliant(result))

    def test_is_compliant_low_coverage(self):
        """Test compliance check with low coverage."""
        result = {
            'missing_dependencies': set(),
            'extra_dependencies': set(),
            'coverage_percentage': 99.0
        }

        self.assertFalse(self.engine.is_compliant(result))


if __name__ == '__main__':
    unittest.main()
