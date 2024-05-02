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
        '42.2',
        '55',
        'some',
        '3.2.1',
    ])
    def test_is_valid_sonar_version_should_return_false_given_invalid_versions(self, invalid_version):
        valid = VersionHelper.is_valid_sonar_version(invalid_version)
        self.assertFalse(valid)

    @parameterized.expand([
        '3.2.1.12345',
    ])
    def test_is_valid_sonar_version_should_return_true_given_valid_versions(self, valid_version):
        valid = VersionHelper.is_valid_sonar_version(valid_version)
        self.assertTrue(valid)

    @parameterized.expand([
        '42.2',
        '55',
        'some',
        '3.2.1.43243',
        '3.2.1',
        '3.2.1-4323',
        '3.2.1#4323',
        '4+3.2.1000',
    ])
    def test_is_valid_plus_signed_version_should_return_false_given_invalid_versions(self, invalid_version):
        valid = VersionHelper.is_valid_plus_signed_version(invalid_version)
        self.assertFalse(valid)

    @parameterized.expand([
        '3.2.1+12345',
    ])
    def test_is_valid_plus_signed_version_should_return_true_given_valid_versions(self, valid_version):
        valid = VersionHelper.is_valid_plus_signed_version(valid_version)
        self.assertTrue(valid)

    @parameterized.expand([
        '42.2',
        '55',
        'some',
        '3.2.1',
        '3+2+2',
    ])
    def test_is_valid_version_should_return_false_given_invalid_versions(self, invalid_version):
        valid = VersionHelper.is_valid_version(invalid_version)
        self.assertFalse(valid)

    @parameterized.expand([
        '3.2.1.12345',
        '3.2.1+12345',
    ])
    def test_is_valid_version_should_return_true_given_valid_versions(self, valid_version):
        valid = VersionHelper.is_valid_version(valid_version)
        self.assertTrue(valid)

    @parameterized.expand([
        ('1.2.3+1234', '1.2.3.1234'),
        ('1.2.1.5433', '1.2.1.5433'),
    ])
    def test_sanitize_version_should_transform_special_version_format_to_standardized_one(self, input_version: str,
                                                                                                 expected_sanitized_version: str):
        actual_sanitized_version = VersionHelper._sanitize_version(input_version)
        self.assertEquals(actual_sanitized_version, expected_sanitized_version)
