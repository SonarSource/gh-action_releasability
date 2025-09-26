# SCA Exceptions

This directory contains false positive and false negative exceptions for SCA (Software Composition Analysis) tools.

## Files

- `false-positives.json`: Dependencies that are detected by SCA but are not actually present
- `false-negatives.json`: Dependencies that are present but not detected by SCA

## Format

Both files use the new JSON format with comments:

```json
{
  "exceptions": [
    {
      "name": "dependency-name-1",
      "comment": "Explanation of why this is a false positive/negative"
    },
    {
      "name": "dependency-name-2",
      "comment": "Another explanation"
    }
  ]
}
```

## Usage

These exceptions are automatically loaded by the releasability checks when running on this repository.

## Documentation

For complete documentation including:

- GitHub integration
- Comment functionality
- Best practices
- Migration guide
- API reference
- Troubleshooting

See: [SCA Exceptions Complete Guide](../SCA_EXCEPTIONS_COMPLETE_GUIDE.md)

## Quick Examples

### False Positives

Dependencies that SCA incorrectly reports as present:

- `commons-io:commons-io` - Detected but not actually used
- `org.apache.commons:commons-lang3` - False positive detection

### False Negatives

Dependencies that are present but SCA doesn't detect:

- `internal-utils:1.0` - Custom dependency not in standard repositories
- `custom-logging:2.0` - Dependency with non-standard naming
