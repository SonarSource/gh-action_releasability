# Reference License Files

This directory contains reference license files used for content-based license validation.

## Purpose

The license content validation system compares actual license files found in software packages against these reference files
to ensure they contain the correct license text. This provides more accurate validation than relying on filename patterns.

## Supported Licenses

The following licenses are currently supported and allowed at SonarSource:

- **Apache-2.0.txt** - Apache License 2.0
- **BSD-2-Clause.txt** - BSD 2-Clause License
- **BSD-3-Clause.txt** - BSD 3-Clause License
- **EPL-1.0.txt** - Eclipse Public License 1.0
- **LGPL-2.1.txt** - GNU Lesser General Public License 2.1
- **LGPL-3.0.txt** - GNU Lesser General Public License 3.0
- **MIT.txt** - MIT License

## Usage

These reference files are automatically loaded by the `LicenseContentValidator` class and used to validate license file content
against expected license types from SBOM (Software Bill of Materials) data.

## Adding New Licenses

To add support for a new license:

1. Add the license text file to this directory with the format `{LICENSE-ID}.txt`
2. Update the `ALLOWED_LICENSES` set in `src/utils/license_content_validator.py`
3. Update this README file

## License File Format

Reference license files should contain the standard license text with placeholders for:

- `[year]` - Copyright year
- `[fullname]` - Copyright holder name
- `[name of copyright owner]` - Alternative copyright holder name

The validation system normalizes these placeholders for comparison.
