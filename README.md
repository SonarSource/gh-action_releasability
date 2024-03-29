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

### Use as a step in another workflow

Within an existing GitHub workflow:

```yaml

...
    steps:
      - uses: SonarSource/gh-action_releasability@0.0.1 <--- replace with last tag
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

## Options

| Option name      | Description                                                                                             | Default |
|------------------|---------------------------------------------------------------------------------------------------------|---------|
| `organization`   | Used to specify the GitHub organization used (i.e: SonarSource)                                         | -       |
| `repository`     | Used to specify the GitHub repository name                                                              | -       |
| `branch`         | Used to specify the GitHub repository branch name                                                       | -       |
| `version`        | Used to specify the version to check (Using Sonar org format: `x.x.x.x` `major.minor.patch.build_number`) | -       |
| `commit-sha`     | Used to specify the GitHub commit sha to use                                                            | -       |
| `ignore-failure` | Used to not fail the gh-action in case of releasability check failure                                   | `false` |

## Versioning

This project is using [Semantic Versioning](https://semver.org/).

The `master` branch shall not be referenced by end-users,
please use tags instead and [Renovate](https://docs.renovatebot.com/) or
[Dependabot](https://docs.github.com/en/code-security/dependabot) to stay up to date.

## Contribute

Contributions are welcome, please have a look at [DEV.md](./DEV.md)
