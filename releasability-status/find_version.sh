#!/bin/bash
# Find last promoted version from GitHub commit status check results:
#   "description": "Latest promoted build of '${PROJECT_VERSION}' from branch '${GITHUB_BRANCH}'"
#   "context": "repox-${GITHUB_BRANCH}",

set -xeuo pipefail

description=$(gh api "/repos/$GITHUB_REPOSITORY/commits/$GITHUB_SHA/status" \
    --jq '.statuses[] | select(.state == "success" and .context == ("repox-'"$GITHUB_REF_NAME"'")).description')
version=$(echo "$description" | cut -d\' -f 2)
if [ -z "${version}" ]; then
  echo "Unable to find promoted version"
  echo "status=skipped" >> "$GITHUB_OUTPUT"
  exit 0
fi

# Validate version format to prevent environment variable injection
# Pattern: [ProjectName-]Major.Minor.Patch[-Mx][.+-]BuildNumber
if [[ ! "$version" =~ ^([a-zA-Z]+-)?[0-9]+\.[0-9]+\.[0-9]+(-M[0-9]+)?[.+-][0-9]+$ ]]; then
  echo "Error: Invalid version format detected: $version"
  echo "Expected format: [ProjectName-]Major.Minor.Patch[-Mx][.+-]BuildNumber"
  echo "Examples: 1.2.3.456, sqs-2025.4.0.111749, project-1.0.0-M1+123, 4.31.0+78266"
  exit 1
fi

echo "version=$version" >> "$GITHUB_OUTPUT"
