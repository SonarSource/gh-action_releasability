# SCA Exceptions Complete Guide

This comprehensive guide covers all aspects of SCA (Software Composition Analysis) exceptions management, including false positives, false negatives,
GitHub integration, and comment functionality.

## Table of Contents

1. [Overview](#overview)
2. [File Format](#file-format)
3. [GitHub Integration](#github-integration)
4. [Comment Functionality](#comment-functionality)
5. [Configuration](#configuration)
6. [Usage Examples](#usage-examples)
7. [Best Practices](#best-practices)
8. [Migration Guide](#migration-guide)
9. [Troubleshooting](#troubleshooting)
10. [API Reference](#api-reference)

## Overview

The SCA exception system helps improve Software Composition Analysis tool accuracy through dogfooding. It supports a two-tier approach:

1. **Global Exceptions**: Stored in the action repository (`.sca-exceptions/` folder)
2. **Repository-Level Exceptions**: Stored in the product repository (`.sca-exceptions/` folder)

Both sets of exceptions are combined and used together during license compliance checking.

### Key Features

- **False Positives (FPs)**: Dependencies detected by SCA but not actually present
- **False Negatives (FNs)**: Dependencies that are present but not detected by SCA
- **Comments**: Detailed explanations for each exception
- **GitHub Integration**: Fetch exceptions from remote repositories
- **Maven Coordinate Normalization**: Smart matching between different naming conventions
- **Backward Compatibility**: Graceful handling of missing files

## File Format

### Required Format

All exception files must use the new format with comments:

```json
{
  "exceptions": [
    {
      "name": "dependency-name",
      "comment": "Explanation of why this is a false positive/negative"
    }
  ]
}
```

### File Structure

#### Action Repository (Global)

gh-action_releasability/
├── .sca-exceptions/
│   ├── false-positives.json
│   ├── false-negatives.json
│   └── README.md

#### Product Repository (Repository-Level)

your-product-repo/
├── .sca-exceptions/
│   ├── false-positives.json
│   ├── false-negatives.json
│   └── README.md

### Example Files

#### false-positives.json

```json
{
  "exceptions": [
    {
      "name": "commons-io:commons-io",
      "comment": "Detected by SCA but not actually used in the codebase"
    },
    {
      "name": "org.apache.commons:commons-lang3",
      "comment": "False positive detection - dependency is not present"
    },
    {
      "name": "com.google.code.gson:gson",
      "comment": "SCA incorrectly reports this dependency as present"
    }
  ]
}
```

#### false-negatives.json

```json
{
  "exceptions": [
    {
      "name": "internal-utils:1.0",
      "comment": "Internal utility library not in public Maven repositories"
    },
    {
      "name": "custom-logging:2.0",
      "comment": "Custom logging framework with non-standard naming convention"
    },
    {
      "name": "legacy-support:0.9",
      "comment": "Legacy support library not in standard repositories, added 2024-01-10"
    }
  ]
}
```

## GitHub Integration

The system automatically loads exceptions from both global and repository-level sources when the `CheckLicenses` check runs.

### Environment Variables

The system uses the following environment variables (automatically set by GitHub Actions):

- `GH_TOKEN`: GitHub personal access token with repository read permissions
- `INPUT_ORGANIZATION`: GitHub organization name (e.g., "SonarSource")
- `INPUT_REPOSITORY`: GitHub repository name (e.g., "sonar-javascript")
- `INPUT_BRANCH`: Git branch/ref (e.g., "master")

### GitHub Token Permissions

The `GH_TOKEN` must have the following permissions:

- `repo` (Full control of private repositories)
  - `repo:status` (Access commit status)
  - `repo_deployment` (Access deployment status)
  - `public_repo` (Access public repositories)

### How It Works

1. **Initialization**: When `SCAExceptionManager` is created, it loads exceptions from both sources
2. **Local Loading**: Loads exceptions from local `.sca-exceptions/` files in the action repository
3. **GitHub Loading**: Uses GitHub API to fetch exceptions from the product repository
4. **Combination**: Merges both sets of exceptions using set union
5. **Usage**: The combined exceptions are used during license compliance checking

### Error Handling

The system is designed to be resilient:

- **Missing GitHub Token**: Falls back to local exceptions only
- **GitHub API Errors**: Logs warning and continues with local exceptions
- **Missing Repository Files**: Gracefully handles 404 responses
- **Invalid JSON**: Logs error and continues with empty set
- **Network Issues**: Logs error and continues with local exceptions

## Comment Functionality

### Benefits of Comments

1. **Documentation**: Explain why each exception exists
2. **Traceability**: Track when and why exceptions were added
3. **Maintenance**: Help teams decide when to remove exceptions
4. **Onboarding**: Help new team members understand the codebase
5. **Auditing**: Provide context for compliance and security reviews

### Comment Guidelines

#### Good Comments

```json
{
  "name": "commons-io:commons-io",
  "comment": "SCA incorrectly detects this dependency due to transitive dependency analysis bug"
}
```

```json
{
  "name": "custom-internal-lib",
  "comment": "Internal library not in public repositories, added to FN list on 2024-01-15"
}
```

#### Bad Comments

```json
{
  "name": "some-dependency",
  "comment": "false positive"
}
```

```json
{
  "name": "another-dependency",
  "comment": "TODO: investigate"
}
```

### Comment Best Practices

1. **Write Clear, Actionable Comments**
2. **Include Context and Dates**
3. **Reference Issues or Documentation**
4. **Explain the Root Cause**
5. **Include Review Dates**

## Configuration

### Automatic Integration

The system automatically loads both global and repository-level exceptions when the `CheckLicenses` check runs.
No additional configuration is required.

### Manual Usage

```python
from utils.sca_exceptions import SCAExceptionManager

# Load exceptions from both global and repository-level sources
manager = SCAExceptionManager(
    repository_root=".",
    github_owner="SonarSource",
    github_repo="sonar-javascript",
    github_ref="master"
)

# Get combined exceptions
fps = manager.get_false_positives()
fns = manager.get_false_negatives()
```

### GitHub Client Usage

```python
from utils.github_client import GitHubClient

# Initialize client
client = GitHubClient(token="your_github_token")

# Test connection
if client.test_connection("SonarSource", "sonar-javascript"):
    # Fetch exceptions
    exceptions = client.get_sca_exceptions("SonarSource", "sonar-javascript", "master")
    print(f"FPs: {len(exceptions['false_positives'])}")
    print(f"FNs: {len(exceptions['false_negatives'])}")
```

## Usage Examples

### Basic Usage

```python
from utils.sca_exceptions import SCAExceptionManager

manager = SCAExceptionManager(repository_root=".")

# Get exception names
fps = manager.get_false_positives()
fns = manager.get_false_negatives()
```

### Detailed Usage with Comments

```python
from utils.sca_exceptions import SCAExceptionManager

manager = SCAExceptionManager(repository_root=".")

# Get detailed exception information including comments
detailed_fps = manager.get_detailed_false_positives()
detailed_fns = manager.get_detailed_false_negatives()

# Process detailed information
for fp in detailed_fps:
    print(f"False Positive: {fp['name']}")
    if fp['comment']:
        print(f"  Comment: {fp['comment']}")
    else:
        print("  Comment: (no comment)")
```

## Best Practices

### 1. Exception Management

- **Global Exceptions**: Use for common, cross-repository issues
- **Repository Exceptions**: Use for product-specific dependencies
- **Documentation**: Document why each exception is needed
- **Regular Review**: Periodically review and clean up exceptions
- **Version Control**: Keep repository-level exceptions in version control

### 2. Comment Quality

- **Be Specific**: Explain the exact reason for the exception
- **Include Context**: Add relevant technical details
- **Add Dates**: Include when the exception was added
- **Reference Issues**: Link to bug reports or documentation
- **Review Regularly**: Set up periodic review of exceptions

### 3. File Organization

- **Consistent Naming**: Use consistent dependency naming conventions
- **Maven Coordinates**: Use full Maven coordinates (groupId:artifactId)
- **Group Related**: Group related exceptions together
- **Clear Structure**: Maintain clear file structure

### 4. Team Collaboration

- **Code Reviews**: Review exception changes in code reviews
- **Documentation**: Keep team documentation up to date
- **Training**: Train team members on exception management
- **Process**: Establish clear processes for adding/removing exceptions

## Migration Guide

### From Legacy Format

If you have existing exception files in the old format, follow these steps:

1. **Backup your files**:

   ```bash
   cp .sca-exceptions/false-positives.json .sca-exceptions/false-positives.json.backup
   cp .sca-exceptions/false-negatives.json .sca-exceptions/false-negatives.json.backup
   ```

2. **Convert the format**:

   ```python
   # Example conversion script
   import json

   # Load legacy format
   with open('.sca-exceptions/false-positives.json', 'r') as f:
       data = json.load(f)

   # Convert to new format
   new_data = {
       "exceptions": [
           {"name": item, "comment": ""} for item in data["exceptions"]
       ]
   }

   # Save new format
   with open('.sca-exceptions/false-positives.json', 'w') as f:
       json.dump(new_data, f, indent=2)
   ```

3. **Add meaningful comments** to each exception

### Migration Checklist

- [ ] Backup existing exception files
- [ ] Convert to new format with comments
- [ ] Test the new format with your CI/CD pipeline
- [ ] Update team documentation
- [ ] Train team members on the new format
- [ ] Set up regular review process for exceptions

## Troubleshooting

### Common Issues

1. **No Exceptions Loaded**: Check GitHub token permissions
2. **Partial Loading**: Check repository name and branch
3. **API Rate Limits**: GitHub API has rate limits (5000 requests/hour)
4. **Network Issues**: Check internet connectivity and firewall settings
5. **Invalid JSON**: Use a JSON validator to check file format
6. **Missing name field**: Ensure all objects have a 'name' field

### Debug Mode

Enable debug logging to see detailed information:

```python
import logging
logging.getLogger('utils.github_client').setLevel(logging.DEBUG)
logging.getLogger('utils.sca_exceptions').setLevel(logging.DEBUG)
```

### Validation

The system validates exception files and provides helpful error messages:

- **Missing name field**: Warns about invalid objects
- **Empty comments**: Accepts empty comments
- **Invalid JSON**: Provides clear error messages
- **Missing files**: Gracefully handles missing files

## API Reference

### SCAExceptionManager

#### Constructor

```python
SCAExceptionManager(
    repository_root: str = ".",
    github_owner: Optional[str] = None,
    github_repo: Optional[str] = None,
    github_ref: str = "master"
)
```

#### Methods

##### get_false_positives() -> Set[str]

Returns the set of false positive dependency names.

##### get_false_negatives() -> Set[str]

Returns the set of false negative dependency names.

##### get_detailed_false_positives() -> List[Dict[str, str]]

Returns detailed false positive information including comments.

##### get_detailed_false_negatives() -> List[Dict[str, str]]

Returns detailed false negative information including comments.

##### is_false_positive(dependency: str) -> bool

Check if a dependency is a known false positive.

##### is_false_negative(dependency: str) -> bool

Check if a dependency is a known false negative.

### GitHubClient

#### Constructor (2)

```python
GitHubClient(token: Optional[str] = None)
```

#### Methods (2)

##### get_file_content(owner: str, repo: str, file_path: str, ref: str = "master") -> Optional[str]

Get the content of a file from a GitHub repository.

##### get_sca_exceptions(owner: str, repo: str, ref: str = "master") -> Dict[str, Set[str]]

Get SCA exceptions from a repository.

##### test_connection(owner: str, repo: str) -> bool

Test if the client can access the repository.

## Logging

The system provides detailed logging:

```bash
INFO - Loaded 5 FPs and 3 FNs from SonarSource/sonar-javascript
INFO - Total loaded: 8 FPs and 6 FNs
INFO -   - Local: 3 FPs, 3 FNs
INFO -   - GitHub: 5 FPs, 3 FNs
```

---

*This guide covers all aspects of SCA exceptions management. For specific implementation details, refer to the source code and test files.*
