"""
Tests for license content validation functionality.
"""

import unittest
import tempfile
import os
from pathlib import Path

from src.utils.license_content_validator import LicenseContentValidator, LicenseContentMatcher


class TestLicenseContentValidator(unittest.TestCase):
    """Test cases for LicenseContentValidator."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for reference licenses
        self.temp_dir = tempfile.mkdtemp()
        self.reference_dir = Path(self.temp_dir) / "reference-licenses"
        self.reference_dir.mkdir()

        # Create test reference licenses
        self._create_test_reference_licenses()

        self.validator = LicenseContentValidator(str(self.reference_dir))

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def _create_test_reference_licenses(self):
        """Create test reference license files."""
        # MIT License
        mit_content = """MIT License

Copyright (c) [year] [fullname]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""

        with open(self.reference_dir / "MIT.txt", "w") as f:
            f.write(mit_content)

        # Apache 2.0 License (simplified)
        apache_content = """Apache License
Version 2.0, January 2004

TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION

1. Definitions.

"License" shall mean the terms and conditions for use, reproduction, and distribution as defined by Sections 1 through 9 of this document.

2. Grant of Copyright License. Subject to the terms and conditions of this License, each Contributor hereby grants to You a perpetual, worldwide, non-exclusive, no-charge, royalty-free, irrevocable copyright license to use, reproduce, modify, merge, publish, distribute, sublicense, and/or sell copies of the Work, and to permit persons to whom the Work is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Work."""

        with open(self.reference_dir / "Apache-2.0.txt", "w") as f:
            f.write(apache_content)

    def test_validate_license_content_exact_match(self):
        """Test validation with exact match."""
        mit_content = """MIT License

Copyright (c) 2023 Test Author

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""

        is_valid, similarity, matched_license = self.validator.validate_license_content(mit_content, "MIT")

        self.assertTrue(is_valid)
        self.assertGreaterEqual(similarity, 0.99)  # Allow for minor whitespace differences
        self.assertEqual(matched_license, "MIT")

    def test_validate_license_content_fuzzy_match(self):
        """Test validation with fuzzy match."""
        # Similar but not identical MIT license
        mit_content = """MIT License

Copyright (c) 2023 Different Author

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""

        is_valid, similarity, matched_license = self.validator.validate_license_content(mit_content, "MIT")

        self.assertTrue(is_valid)
        self.assertGreater(similarity, 0.8)
        self.assertEqual(matched_license, "MIT")

    def test_validate_license_content_no_match(self):
        """Test validation with no match."""
        random_content = "This is not a license at all. Just some random text."

        is_valid, similarity, matched_license = self.validator.validate_license_content(random_content, "MIT")

        self.assertFalse(is_valid)
        self.assertLess(similarity, 0.8)

    def test_validate_license_content_unknown_license(self):
        """Test validation with unknown license type."""
        mit_content = "MIT License content here..."

        is_valid, similarity, matched_license = self.validator.validate_license_content(mit_content, "Unknown-License")

        self.assertFalse(is_valid)
        self.assertEqual(similarity, 0.0)
        self.assertIn("Unknown license type", matched_license)

    def test_validate_license_file(self):
        """Test validation of license file."""
        # Create a temporary license file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("""MIT License

Copyright (c) 2023 Test Author

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.""")
            temp_file = f.name

        try:
            is_valid, similarity, matched_license = self.validator.validate_license_file(temp_file, "MIT")

            self.assertTrue(is_valid)
            self.assertGreaterEqual(similarity, 0.99)  # Allow for minor whitespace differences
            self.assertEqual(matched_license, "MIT")
        finally:
            os.unlink(temp_file)

    def test_get_available_licenses(self):
        """Test getting available reference licenses."""
        available = self.validator.get_available_licenses()

        self.assertIn("MIT", available)
        self.assertIn("Apache-2.0", available)

    def test_get_allowed_licenses(self):
        """Test getting allowed licenses."""
        allowed = self.validator.get_allowed_licenses()

        self.assertIn("MIT", allowed)
        self.assertIn("Apache-2.0", allowed)
        self.assertIn("LGPL-2.1", allowed)


class TestLicenseContentMatcher(unittest.TestCase):
    """Test cases for LicenseContentMatcher."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for reference licenses
        self.temp_dir = tempfile.mkdtemp()
        self.reference_dir = Path(self.temp_dir) / "reference-licenses"
        self.reference_dir.mkdir()

        # Create test reference licenses
        self._create_test_reference_licenses()

        self.validator = LicenseContentValidator(str(self.reference_dir))
        self.matcher = LicenseContentMatcher(self.validator)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def _create_test_reference_licenses(self):
        """Create test reference license files."""
        # MIT License
        mit_content = """MIT License

Copyright (c) [year] [fullname]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""

        with open(self.reference_dir / "MIT.txt", "w") as f:
            f.write(mit_content)

    def test_match_licenses_to_components(self):
        """Test matching licenses to SBOM components."""
        extracted_licenses = {
            'test-artifact.jar': [
                {
                    'type': 'third_party',
                    'name': 'Newtonsoft.Json-LICENSE.txt',
                    'content': """MIT License

Copyright (c) 2023 James Newton-King

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.""",
                    'path': '/licenses/THIRD_PARTY_LICENSES/Newtonsoft.Json-LICENSE.txt'
                }
            ]
        }

        sbom_components = [
            {
                'name': 'Newtonsoft.Json',
                'licenses': [{'id': 'MIT'}]
            },
            {
                'name': 'SomeOther.Library',
                'licenses': [{'id': 'Apache-2.0'}]
            }
        ]

        results = self.matcher.match_licenses_to_components(extracted_licenses, sbom_components)

        self.assertEqual(len(results['matched_licenses']), 1)
        self.assertEqual(len(results['unmatched_licenses']), 0)
        self.assertEqual(len(results['validation_errors']), 0)
        self.assertEqual(results['coverage_percentage'], 50.0)  # 1 out of 2 components matched

        match = results['matched_licenses'][0]
        self.assertEqual(match['component_name'], 'Newtonsoft.Json')
        self.assertEqual(match['expected_license'], 'MIT')
        self.assertEqual(match['matched_license'], 'MIT')

    def test_extract_dependency_name_from_license_file(self):
        """Test extracting dependency name from license filename."""
        # Test with standard format
        name = self.matcher._extract_dependency_name_from_license_file("Newtonsoft.Json-LICENSE.txt")
        self.assertEqual(name, "Newtonsoft.Json")

        # Test with different format
        name = self.matcher._extract_dependency_name_from_license_file("SomeLibrary-LICENSE.txt")
        self.assertEqual(name, "SomeLibrary")

        # Test with invalid format
        name = self.matcher._extract_dependency_name_from_license_file("InvalidFormat.txt")
        self.assertIsNone(name)

    def test_names_match(self):
        """Test name matching logic."""
        # Test exact match
        self.assertTrue(self.matcher._names_match("Newtonsoft.Json", "Newtonsoft.Json"))

        # Test case insensitive match
        self.assertTrue(self.matcher._names_match("newtonsoft.json", "Newtonsoft.Json"))

        # Test with special characters
        self.assertTrue(self.matcher._names_match("Newtonsoft.Json", "Newtonsoft-Json"))

        # Test no match
        self.assertFalse(self.matcher._names_match("Newtonsoft.Json", "DifferentLibrary"))


if __name__ == '__main__':
    unittest.main()
