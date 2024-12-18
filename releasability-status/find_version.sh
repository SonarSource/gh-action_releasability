#!/bin/bash
# Find last promoted version from GitHub commit status check results:
#   "description": "Latest promoted build of '${PROJECT_VERSION}' from branch '${GITHUB_BRANCH}'"
#   "context": "repox-${GITHUB_BRANCH}",

set -xeuo pipefail

description=$(gh api "/repos/$GITHUB_REPOSITORY/commits/$GITHUB_SHA/statuses" \
    --jq '.[] | select(.state == "success" and .context == ("repox-'"$GITHUB_REF_NAME"'")) | .description')
version=$(echo "$description" | cut -d\' -f 2)
if [ -z "${version}" ]; then
  echo "Unable to find promoted version"
  echo "status=skipped" >> "$GITHUB_OUTPUT"
  exit 0
fi
echo "version=$version" >> "$GITHUB_OUTPUT"
