#!/bin/bash
# Find last promoted version from github commit status check results
set -xeuo pipefail

version=""

readarray -t statuses < <(echo "$OUTPUTS" | jq -c ".statuses[]")
for i in "${statuses[@]}"; do
  desc=$(echo "$i" | jq -r ".description")
  v=$(echo "$desc" | cut -d\' -f 2 )
  branch=$(echo "$desc" | cut -d\' -f 4 )
  if [[ $branch == "$1" ]]; then
    version=$v
    break
  fi
done

if [ -z "${version}" ]; then
  echo "Unable to find promoted version"
  exit 1
fi

echo "version=$version" >> "$GITHUB_OUTPUT"
