import unittest

from parameterized import parameterized
from utils.version_helper import VersionHelper


class VersionHelperTest(unittest.TestCase):

    @parameterized.expand([
        '1.2.3',
        '42.2',
        '5.4.3.2.1'
    ])
    def test_extract_build_number_should_raise_an_exception_given_the_provided_version_is_not_valid(self, invalid_version: str):
        with self.assertRaises(ValueError):
            VersionHelper.extract_build_number(invalid_version)

    @parameterized.expand([
        ('1.2.3.1234', 1234),
        ('42.2.1.5433', 5433),
    ])
    def test_extract_build_number_should_return_the_expected_build_number_given_valid_versions(self, valid_version: str,
                                                                                               expected_build_number: int):
        actual_build_number = VersionHelper.extract_build_number(valid_version)
        self.assertEquals(actual_build_number, expected_build_number)

    @parameterized.expand([
        ('1.2.3+1234', 1234),
        ('42.2.1+5433', 5433),
    ])
    def test_extract_build_number_should_return_the_expected_build_number_given_special_versions(self, valid_version: str,
                                                                                                 expected_build_number: int):
        actual_build_number = VersionHelper.extract_build_number(valid_version)
        self.assertEquals(actual_build_number, expected_build_number)

    @parameterized.expand([
        ('1.2.3-1234', 1234),
        ('42.2.1-5433', 5433),
    ])
    def test_extract_build_number_should_return_the_expected_build_number_given_npm_friendly_versions(self, valid_version: str,
                                                                                                 expected_build_number: int):
        actual_build_number = VersionHelper.extract_build_number(valid_version)
        self.assertEquals(actual_build_number, expected_build_number)

    @parameterized.expand([
        '42.2',
        '55',
        'some',
        '3.2.1',
        '3+2+2',
        '3.2.1#4323',
        '4+3.2.1000',
        'proj--3.2.1+1234',
        'proj-3.2.1-MX+1234',
    ])
    def test_is_valid_sonar_version_should_raise_exception_given_invalid_versions(self, invalid_version):
        with self.assertRaises(ValueError):
            VersionHelper.validate_version(invalid_version)

    @parameterized.expand([
        '3.2.1.12345',
        'proj-3.2.1.12345',
        '3.2.1-M99.12345',
        '3.2.1+12345',
        '3.2.1-12345',
        'proj-3.2.1-M99.12345',
    ])
    def test_is_valid_sonar_version_should_raise_no_exception_given_valid_versions(self, valid_version):
        VersionHelper.validate_version(valid_version)
