# SonarSource GitHub Action for releasability checks

![GitHub Release](https://img.shields.io/github/v/release/SonarSource/gh-action_releasability)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=SonarSource_gh-action_releasability&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=SonarSource_gh-action_releasability)
[![.github/workflows/it-test.yml](https://github.com/SonarSource/gh-action_releasability/actions/workflows/it-test.yml/badge.svg)](https://github.com/SonarSource/gh-action_releasability/actions/workflows/it-test.yml)

Trigger [ops-releasability checks](https://github.com/SonarSource/ops-releasability) and collect results.

## Usage

### Verify that all releasability checks pass before actually doing a new release

Trigger manually:
[releasability_checks.yml](https://github.com/SonarSource/gh-action_releasability/actions/workflows/releasability_checks.yml)

![Form](doc/assets/releasability_checks_workflow_dispatch.png)

List of [parameters](#options)

### Show current releasability status in default branch

To show releasability status of the latest promoted version from the default branch,

```yaml
name: Releasability status
'on':
    check_suite:
        types:
            - completed
jobs:
    update_releasability_status:
        runs-on: ubuntu-latest
        name: Releasability status
        permissions:
            id-token: write
            statuses: write
            contents: read
        if: >-
            (contains(fromJSON('["main", "master"]'),
            github.event.check_suite.head_branch) ||
            startsWith(github.event.check_suite.head_branch, 'dogfood-') ||
            startsWith(github.event.check_suite.head_branch, 'branch-')) &&
            github.event.check_suite.conclusion == 'success' &&
            github.event.check_suite.app.slug == 'cirrus-ci'
        steps:
            -   uses: >-
                    SonarSource/gh-action_releasability/releasability-status@v2
                with:
                    optional_checks: "Jira"
                env:
                    GITHUB_TOKEN: '${{ secrets.GITHUB_TOKEN }}'
```

This will run the releasability checks once the Cirrus tasks are completed and update the commit status as below.

![Releasability status](doc/assets/releasability_status.png)

The parameter `optional_checks` is optional. You can provide a comma-separated list of checks to be treated as
optional while doing releasability checks. Failure in any of these checks will not mark the commit status as red,
but provide the details in commit status description.

This will be helpful in case you have a few checks which are expected to fail until the day of the Release.
Eg: Jira check will fail until the release, since there will be work-in-progress tickets throughout the sprint.
If you add this parameter, make sure to check the description for failed optional checks before triggering an actual release.

![Releasability optional checks](doc/assets/releasability_optional.png)

### List of checks

Please refer to
the [End-User documentation](https://xtranet-sonarsource.atlassian.net/wiki/spaces/Platform/pages/3309240895/End-user+Documentation+-+Releasability)
for a list of checks and their description.

> [!WARNING]
> Releasability status checks will not work if you have Merge queue enabled on the repository

## Use as a step in another workflow

Within an existing GitHub workflow:

```yaml

...
steps:
    -   uses: SonarSource/gh-action_releasability@v2
        id: releasability-checks
        with:
            organization:
            repository:
            branch:
            version:
            commit-sha:
```

The following permission is required:

```yaml
permissions:
    id-token: write
```

### Options

| Option name       | Description                                                                     | Default |
|-------------------|---------------------------------------------------------------------------------|---------|
| `organization`    | The GitHub organization used (i.e: SonarSource)                                 | -       |
| `repository`      | The GitHub repository name                                                      | -       |
| `branch`          | The GitHub repository branch name                                               | -       |
| `version`         | The version to check (`[prefix-]major.minor.patch.build_number`)                | -       |
| `commit-sha`      | The GitHub commit SHA                                                           | -       |
| `ignore-failure`  | Whether to fail or not the GitHub action in case of Releasability check failure | `false` |
| `releasabily-env` | For development purposes, the environment to use (`prod`, `staging`, or `dev`)  | `prod`  |

## Development

### Versioning

This project is using [Semantic Versioning](https://semver.org/).

The `master` branch shall not be referenced by end-users.

If you use [Renovate](https://docs.renovatebot.com/) or [Dependabot](https://docs.github.com/en/code-security/dependabot),
use the latest released tag.

Alternatively, use the `v*` branches which will kept up-to-date with latest released tag

### Releasing

Create a new release on [GitHub](https://github.com/SonarSource/gh-action_releasability/releases)
following semantic versioning.

To update the v-branch,
run the [Update v-branch workflow](https://github.com/SonarSource/gh-action_releasability/actions/workflows/update-v-branch.yml).
The workflow will update the v-branch to the specified tag.

### Contribute

Contributions are welcome, please have a look at [DEV.md](./DEV.md)

### Testing

Use the `releasabily-env` option to test the action with a different AWS account (staging or development).
