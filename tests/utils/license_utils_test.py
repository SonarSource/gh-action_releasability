"""
Unit tests for license_utils.py module.
"""

import unittest
import tempfile
import os
import shutil
import zipfile
import json
from unittest.mock import patch, MagicMock

# Adjust path for local imports
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from utils.license_utils import LicenseExtractor, LicenseComparator, LPSValidator


class TestLicenseExtractor(unittest.TestCase):

    def setUp(self):
        self.extractor = LicenseExtractor()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_extract_licenses_from_artifacts_empty_list(self):
        """Test extraction with empty artifact list."""
        result = self.extractor.extract_licenses_from_artifacts([])
        self.assertEqual(result, {})

    def test_extract_licenses_from_artifacts_nonexistent_file(self):
        """Test extraction with non-existent artifact file."""
        artifacts = [{'path': '/nonexistent/file.jar', 'name': 'test.jar'}]
        result = self.extractor.extract_licenses_from_artifacts(artifacts)
        self.assertEqual(result['test.jar'], [])

    def test_extract_licenses_from_artifacts_unsupported_format(self):
        """Test extraction with unsupported file format."""
        # Create a dummy file with unsupported extension
        dummy_file = os.path.join(self.temp_dir, 'test.txt')
        with open(dummy_file, 'w') as f:
            f.write('dummy content')

        artifacts = [{'path': dummy_file, 'name': 'test.txt'}]
        result = self.extractor.extract_licenses_from_artifacts(artifacts)
        self.assertEqual(result['test.txt'], [])

    def test_extract_from_archive_with_licenses(self):
        """Test extraction from archive with proper license structure."""
        # Create a test JAR with license structure
        jar_path = os.path.join(self.temp_dir, 'test.jar')
        with zipfile.ZipFile(jar_path, 'w') as jar:
            # Add main LICENSE.txt
            jar.writestr('licenses/LICENSE.txt', 'Main license content')
            # Add third-party licenses
            jar.writestr('licenses/THIRD_PARTY_LICENSES/LibraryA-LICENSE.txt', 'Library A license')
            jar.writestr('licenses/THIRD_PARTY_LICENSES/LibraryB-LICENSE.txt', 'Library B license')

        artifacts = [{'path': jar_path, 'name': 'test.jar'}]
        result = self.extractor.extract_licenses_from_artifacts(artifacts)

        self.assertIn('test.jar', result)
        licenses = result['test.jar']
        self.assertEqual(len(licenses), 3)  # 1 main + 2 third-party

        # Check main license
        main_licenses = [l for l in licenses if l['type'] == 'main']
        self.assertEqual(len(main_licenses), 1)
        self.assertEqual(main_licenses[0]['name'], 'LICENSE.txt')

        # Check third-party licenses
        third_party_licenses = [l for l in licenses if l['type'] == 'third_party']
        self.assertEqual(len(third_party_licenses), 2)
        license_names = [l['name'] for l in third_party_licenses]
        self.assertIn('LibraryA-LICENSE.txt', license_names)
        self.assertIn('LibraryB-LICENSE.txt', license_names)

    def test_extract_from_archive_with_inner_archives(self):
        """Test extraction from archive with inner archives."""
        # Create a test JAR with inner ZIP
        jar_path = os.path.join(self.temp_dir, 'test.jar')
        with zipfile.ZipFile(jar_path, 'w') as jar:
            # Add main licenses
            jar.writestr('licenses/LICENSE.txt', 'Main license')
            jar.writestr('licenses/THIRD_PARTY_LICENSES/LibraryA-LICENSE.txt', 'Library A license')

            # Add inner ZIP with its own licenses
            inner_zip_content = self._create_inner_zip_content()
            jar.writestr('inner.zip', inner_zip_content)

        artifacts = [{'path': jar_path, 'name': 'test.jar'}]
        result = self.extractor.extract_licenses_from_artifacts(artifacts)

        self.assertIn('test.jar', result)
        licenses = result['test.jar']

        # Should have main licenses + inner archive licenses
        self.assertGreater(len(licenses), 2)

        # Check for inner archive licenses
        inner_licenses = [l for l in licenses if 'inner' in l['source']]
        self.assertGreater(len(inner_licenses), 0)

    def test_extract_from_archive_with_inner_tgz_archives(self):
        """Test extraction from archive with inner TGZ archives."""
        # Create a test JAR with inner TGZ
        jar_path = os.path.join(self.temp_dir, 'test.jar')
        with zipfile.ZipFile(jar_path, 'w') as jar:
            # Add main licenses
            jar.writestr('licenses/LICENSE.txt', 'Main license')
            jar.writestr('licenses/THIRD_PARTY_LICENSES/LibraryA-LICENSE.txt', 'Library A license')

            # Add inner TGZ with its own licenses
            inner_tgz_content = self._create_inner_tgz_content()
            jar.writestr('inner.tgz', inner_tgz_content)

        artifacts = [{'path': jar_path, 'name': 'test.jar'}]
        result = self.extractor.extract_licenses_from_artifacts(artifacts)

        self.assertIn('test.jar', result)
        licenses = result['test.jar']

        # Should have main licenses + inner archive licenses
        self.assertGreater(len(licenses), 2)

        # Check for inner archive licenses
        inner_licenses = [l for l in licenses if 'inner' in l['source']]
        self.assertGreater(len(inner_licenses), 0)

    def _create_inner_zip_content(self):
        """Create inner ZIP content for testing."""
        import io
        inner_zip = io.BytesIO()
        with zipfile.ZipFile(inner_zip, 'w') as zip_file:
            zip_file.writestr('licenses/LICENSE.txt', 'Inner main license')
            zip_file.writestr('licenses/THIRD_PARTY_LICENSES/InnerLibrary-LICENSE.txt', 'Inner library license')
        return inner_zip.getvalue()

    def _create_inner_tgz_content(self):
        """Create inner TGZ content for testing."""
        import io
        import tarfile
        inner_tgz = io.BytesIO()
        with tarfile.open(fileobj=inner_tgz, mode='w:gz') as tgz_file:
            # Add license files to the TGZ
            license_txt = tarfile.TarInfo(name='licenses/LICENSE.txt')
            license_txt.size = len(b'Inner TGZ main license')
            tgz_file.addfile(license_txt, io.BytesIO(b'Inner TGZ main license'))

            third_party_license = tarfile.TarInfo(name='licenses/THIRD_PARTY_LICENSES/InnerTgzLibrary-LICENSE.txt')
            third_party_license.size = len(b'Inner TGZ library license')
            tgz_file.addfile(third_party_license, io.BytesIO(b'Inner TGZ library license'))

        return inner_tgz.getvalue()

    def test_extract_licenses_from_directory(self):
        """Test extraction from a licenses directory."""
        # Create licenses directory structure
        licenses_dir = os.path.join(self.temp_dir, 'licenses')
        os.makedirs(licenses_dir)

        # Create main LICENSE.txt
        main_license_path = os.path.join(licenses_dir, 'LICENSE.txt')
        with open(main_license_path, 'w') as f:
            f.write('Main license content')

        # Create THIRD_PARTY_LICENSES directory
        third_party_dir = os.path.join(licenses_dir, 'THIRD_PARTY_LICENSES')
        os.makedirs(third_party_dir)

        # Create third-party license files
        with open(os.path.join(third_party_dir, 'LibraryA-LICENSE.txt'), 'w') as f:
            f.write('Library A license')
        with open(os.path.join(third_party_dir, 'LibraryB-LICENSE.txt'), 'w') as f:
            f.write('Library B license')

        licenses = self.extractor._extract_licenses_from_directory(licenses_dir, 'test')

        self.assertEqual(len(licenses), 3)  # 1 main + 2 third-party

        # Check main license
        main_licenses = [l for l in licenses if l['type'] == 'main']
        self.assertEqual(len(main_licenses), 1)
        self.assertEqual(main_licenses[0]['content'], 'Main license content')

        # Check third-party licenses
        third_party_licenses = [l for l in licenses if l['type'] == 'third_party']
        self.assertEqual(len(third_party_licenses), 2)

    def test_extract_from_nupkg_archive_with_licenses(self):
        """Test extraction from NUPKG archive with proper license structure."""
        # Create a test NUPKG with license structure
        nupkg_path = os.path.join(self.temp_dir, 'test.nupkg')
        with zipfile.ZipFile(nupkg_path, 'w') as nupkg:
            # Add main LICENSE.txt
            nupkg.writestr('licenses/LICENSE.txt', 'Main license content')
            # Add third-party licenses
            nupkg.writestr('licenses/THIRD_PARTY_LICENSES/LibraryA-LICENSE.txt', 'Library A license')
            nupkg.writestr('licenses/THIRD_PARTY_LICENSES/LibraryB-LICENSE.txt', 'Library B license')

        artifacts = [{'path': nupkg_path, 'name': 'test.nupkg'}]
        result = self.extractor.extract_licenses_from_artifacts(artifacts)

        self.assertIn('test.nupkg', result)
        licenses = result['test.nupkg']
        self.assertEqual(len(licenses), 3)  # 1 main + 2 third-party

        # Check main license
        main_licenses = [l for l in licenses if l['type'] == 'main']
        self.assertEqual(len(main_licenses), 1)
        self.assertEqual(main_licenses[0]['name'], 'LICENSE.txt')

        # Check third-party licenses
        third_party_licenses = [l for l in licenses if l['type'] == 'third_party']
        self.assertEqual(len(third_party_licenses), 2)
        license_names = [l['name'] for l in third_party_licenses]
        self.assertIn('LibraryA-LICENSE.txt', license_names)
        self.assertIn('LibraryB-LICENSE.txt', license_names)

    def test_extract_from_archive_with_inner_nupkg_archives(self):
        """Test extraction from archive with inner NUPKG archives."""
        # Create a test JAR with inner NUPKG
        jar_path = os.path.join(self.temp_dir, 'test.jar')
        with zipfile.ZipFile(jar_path, 'w') as jar:
            # Add main LICENSE.txt
            jar.writestr('licenses/LICENSE.txt', 'Main license content')
            # Add inner NUPKG with licenses
            inner_nupkg_content = self._create_inner_nupkg_content()
            jar.writestr('inner.nupkg', inner_nupkg_content)

        artifacts = [{'path': jar_path, 'name': 'test.jar'}]
        result = self.extractor.extract_licenses_from_artifacts(artifacts)

        self.assertIn('test.jar', result)
        licenses = result['test.jar']

        # Should have main license + inner NUPKG licenses
        self.assertGreater(len(licenses), 1)

        # Check for inner archive licenses
        inner_licenses = [l for l in licenses if 'inner' in l['source']]
        self.assertGreater(len(inner_licenses), 0)

    def _create_inner_nupkg_content(self):
        """Create inner NUPKG content for testing."""
        import io
        inner_nupkg = io.BytesIO()
        with zipfile.ZipFile(inner_nupkg, 'w') as nupkg_file:
            nupkg_file.writestr('licenses/LICENSE.txt', 'Inner main license')
            nupkg_file.writestr('licenses/THIRD_PARTY_LICENSES/InnerLibrary-LICENSE.txt', 'Inner library license')
        return inner_nupkg.getvalue()


class TestLicenseComparator(unittest.TestCase):

    def setUp(self):
        self.comparator = LicenseComparator(".", github_owner="test-org", github_repo="test-repo", github_ref="master", reference_licenses_dir="src/resources/reference-licenses")

    def test_load_sbom(self):
        """Test loading SBOM data."""
        sbom_data = {
            'components': [
                {'name': 'LibraryA', 'version': '1.0.0'},
                {'name': 'LibraryB', 'version': '2.0.0'},
                {'name': 'LibraryC', 'version': '3.0.0'}
            ]
        }

        self.comparator.load_sbom(sbom_data)
        self.assertEqual(len(self.comparator.sbom_components), 3)

    def test_compare_licenses_with_sbom_perfect_match(self):
        """Test comparison with perfect match between licenses and SBOM."""
        # Load SBOM with license information
        sbom_data = {
            'components': [
                {'name': 'LibraryA', 'version': '1.0.0', 'licenses': [{'expression': 'MIT'}]},
                {'name': 'LibraryB', 'version': '2.0.0', 'licenses': [{'expression': 'MIT'}]}
            ]
        }
        self.comparator.load_sbom(sbom_data)

        # Create extracted licenses with proper MIT license content (using reference content)
        with open('src/resources/reference-licenses/MIT.txt', 'r') as f:
            mit_license_content = f.read()

        extracted_licenses = {
            'test.jar': [
                {'type': 'main', 'name': 'LICENSE.txt', 'content': 'Main license'},
                {'type': 'third_party', 'name': 'LibraryA-LICENSE.txt', 'content': mit_license_content},
                {'type': 'third_party', 'name': 'LibraryB-LICENSE.txt', 'content': mit_license_content}
            ]
        }

        result = self.comparator.compare_licenses_with_sbom(extracted_licenses)

        self.assertEqual(result['total_artifacts'], 1)
        self.assertEqual(result['total_licenses_found'], 2)
        self.assertEqual(result['total_sbom_components'], 2)
        # With enhanced comparison, we expect perfect match
        self.assertEqual(len(result['matched_licenses']), 2)
        self.assertEqual(len(result['missing_licenses']), 0)
        self.assertEqual(len(result['extra_licenses']), 0)
        self.assertEqual(result['coverage_percentage'], 100.0)
        self.assertTrue(result['is_compliant'])

    def test_compare_licenses_with_sbom_missing_licenses(self):
        """Test comparison with missing licenses."""
        # Load SBOM with license information
        sbom_data = {
            'components': [
                {'name': 'LibraryA', 'version': '1.0.0', 'licenses': [{'expression': 'MIT'}]},
                {'name': 'LibraryB', 'version': '2.0.0', 'licenses': [{'expression': 'MIT'}]},
                {'name': 'LibraryC', 'version': '3.0.0', 'licenses': [{'expression': 'MIT'}]}
            ]
        }
        self.comparator.load_sbom(sbom_data)

        # Create extracted licenses with proper MIT license content (missing LibraryC)
        with open('src/resources/reference-licenses/MIT.txt', 'r') as f:
            mit_license_content = f.read()

        extracted_licenses = {
            'test.jar': [
                {'type': 'main', 'name': 'LICENSE.txt', 'content': 'Main license'},
                {'type': 'third_party', 'name': 'LibraryA-LICENSE.txt', 'content': mit_license_content},
                {'type': 'third_party', 'name': 'LibraryB-LICENSE.txt', 'content': mit_license_content}
            ]
        }

        result = self.comparator.compare_licenses_with_sbom(extracted_licenses)

        self.assertEqual(len(result['matched_licenses']), 2)
        self.assertEqual(len(result['missing_licenses']), 1)
        self.assertIn('LibraryC', result['missing_licenses'])
        self.assertAlmostEqual(result['coverage_percentage'], 66.7, places=1)

    def test_compare_licenses_with_sbom_extra_licenses(self):
        """Test comparison with extra licenses not in SBOM."""
        # Load SBOM with license information
        sbom_data = {
            'components': [
                {'name': 'LibraryA', 'version': '1.0.0', 'licenses': [{'expression': 'MIT'}]}
            ]
        }
        self.comparator.load_sbom(sbom_data)

        # Create extracted licenses with proper MIT license content (extra LibraryB)
        with open('src/resources/reference-licenses/MIT.txt', 'r') as f:
            mit_license_content = f.read()

        extracted_licenses = {
            'test.jar': [
                {'type': 'main', 'name': 'LICENSE.txt', 'content': 'Main license'},
                {'type': 'third_party', 'name': 'LibraryA-LICENSE.txt', 'content': mit_license_content},
                {'type': 'third_party', 'name': 'LibraryB-LICENSE.txt', 'content': mit_license_content}
            ]
        }

        result = self.comparator.compare_licenses_with_sbom(extracted_licenses)

        self.assertEqual(len(result['matched_licenses']), 1)
        self.assertEqual(len(result['missing_licenses']), 0)
        self.assertEqual(len(result['extra_licenses']), 1)
        self.assertIn('LibraryB-LICENSE.txt', result['extra_licenses'])

    def test_extract_component_names(self):
        """Test extraction of component names from SBOM."""
        self.comparator.sbom_components = [
            {'name': 'LibraryA', 'version': '1.0.0'},
            {'name': 'LibraryB', 'version': '2.0.0'},
            {'name': '', 'version': '3.0.0'},  # Empty name
            {'name': 'LibraryC', 'version': '4.0.0'}
        ]

        names = self.comparator._extract_component_names()
        self.assertEqual(names, ['LibraryA', 'LibraryB', 'LibraryC'])

    def test_extract_license_names(self):
        """Test extraction of license names from license files."""
        licenses = [
            {'name': 'LibraryA-LICENSE.txt'},
            {'name': 'LibraryB_LICENSE.txt'},
            {'name': 'LibraryC.txt'},
            {'name': 'LICENSE.txt'}  # Should be ignored
        ]

        names = self.comparator._extract_license_names(licenses)
        expected_names = {'LibraryA', 'LibraryB', 'LibraryC'}
        actual_names = set(names)
        # Remove 'LICENSE' which comes from 'LICENSE.txt'
        actual_names.discard('LICENSE')
        self.assertEqual(actual_names, expected_names)


class TestLPSValidator(unittest.TestCase):

    def setUp(self):
        self.validator = LPSValidator(".", github_owner="test-org", github_repo="test-repo", github_ref="master", reference_licenses_dir="src/resources/reference-licenses")

    def test_validate_artifacts_empty_list(self):
        """Test validation with empty artifact list."""
        result = self.validator.validate_artifacts([])

        self.assertTrue(result['lps_compliant'])
        self.assertEqual(result['artifacts_processed'], 0)
        self.assertEqual(result['licenses_extracted'], {})
        self.assertIsNone(result['sbom_comparison'])
        self.assertEqual(len(result['issues']), 0)

    def test_validate_artifacts_with_sbom(self):
        """Test validation with SBOM data."""
        # Mock the extractor to return test data with proper MIT license content
        with open('src/resources/reference-licenses/MIT.txt', 'r') as f:
            mit_license_content = f.read()

        with patch.object(self.validator.extractor, 'extract_licenses_from_artifacts') as mock_extract:
            mock_extract.return_value = {
                'test.jar': [
                    {'type': 'main', 'name': 'LICENSE.txt', 'content': 'Main license', 'path': '/licenses/LICENSE.txt'},
                    {'type': 'third_party', 'name': 'LibraryA-LICENSE.txt', 'content': mit_license_content, 'path': '/licenses/THIRD_PARTY_LICENSES/LibraryA-LICENSE.txt'}
                ]
            }

            sbom_data = {
                'components': [
                    {'name': 'LibraryA', 'version': '1.0.0', 'licenses': [{'expression': 'MIT'}]},
                    {'name': 'LibraryB', 'version': '2.0.0', 'licenses': [{'expression': 'MIT'}]}
                ]
            }

            result = self.validator.validate_artifacts([{'path': 'test.jar', 'name': 'test.jar'}], sbom_data)

            self.assertFalse(result['lps_compliant'])  # Should fail due to missing LibraryB
            self.assertEqual(result['artifacts_processed'], 1)
            self.assertIsNotNone(result['sbom_comparison'])
            self.assertIn('Missing licenses for 1 SBOM components', result['issues'])

    def test_check_lps_compliance_missing_main_license(self):
        """Test LPS compliance check with missing main license."""
        extracted_licenses = {
            'test.jar': [
                {'type': 'third_party', 'name': 'LibraryA-LICENSE.txt', 'content': 'Library A license', 'path': '/licenses/THIRD_PARTY_LICENSES/LibraryA-LICENSE.txt'}
            ]
        }

        issues = self.validator._check_lps_compliance(extracted_licenses)
        self.assertIn('Missing main LICENSE.txt in test.jar', issues)

    def test_check_lps_compliance_missing_third_party_licenses(self):
        """Test LPS compliance check with missing third-party licenses."""
        extracted_licenses = {
            'test.jar': [
                {'type': 'main', 'name': 'LICENSE.txt', 'content': 'Main license', 'path': '/licenses/LICENSE.txt'}
            ]
        }

        issues = self.validator._check_lps_compliance(extracted_licenses)
        self.assertIn('No third-party licenses found in test.jar', issues)

    def test_check_lps_compliance_missing_licenses_directory(self):
        """Test LPS compliance check with missing licenses directory."""
        extracted_licenses = {
            'test.jar': [
                {'type': 'main', 'name': 'LICENSE.txt', 'content': 'Main license', 'path': '/some/other/path/LICENSE.txt'}
            ]
        }

        issues = self.validator._check_lps_compliance(extracted_licenses)
        self.assertIn('No licenses/ directory found in test.jar', issues)

    def test_check_lps_compliance_compliant(self):
        """Test LPS compliance check with compliant structure."""
        extracted_licenses = {
            'test.jar': [
                {'type': 'main', 'name': 'LICENSE.txt', 'content': 'Main license', 'path': '/licenses/LICENSE.txt'},
                {'type': 'third_party', 'name': 'LibraryA-LICENSE.txt', 'content': 'Library A license', 'path': '/licenses/THIRD_PARTY_LICENSES/LibraryA-LICENSE.txt'}
            ]
        }

        issues = self.validator._check_lps_compliance(extracted_licenses)
        self.assertEqual(len(issues), 0)


if __name__ == '__main__':
    unittest.main()
