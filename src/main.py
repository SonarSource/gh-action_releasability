import os
import sys

from releasability.releasability_service import ReleasabilityService
from utils.github_action_helper import GithubActionHelper
from github_action_utils import error, notice, set_output


def do_releasability_checks(organization: str, repository: str, branch: str, version: str, commit_sha: str):
    try:
        releasability = ReleasabilityService()

        # Start both inline and lambda checks
        correlation_id, inline_results = releasability.start_releasability_checks(
            organization,
            repository,
            branch,
            version,
            commit_sha
        )

        # Get combined report with both inline and lambda results
        report = releasability.get_combined_report(correlation_id, inline_results)
        GithubActionHelper.set_output_logs(str(report))

        for check in report.get_checks():
            name = f'releasability{check.name}'
            set_output(name, check.state)

        if report.contains_error():
            error(f"Releasability checks of {version} failed")
            GithubActionHelper.set_output_status("1")
        else:
            notice(f"Releasability checks of {version} passed successfully")
            GithubActionHelper.set_output_status("0")

    except Exception as ex:
        error(f"{ex}")
        GithubActionHelper.set_output_status("1")
        sys.exit(1)


if __name__ == "__main__":
    do_releasability_checks(
        organization=os.getenv("INPUT_ORGANIZATION"),
        repository=os.getenv("INPUT_REPOSITORY"),
        branch=os.getenv("INPUT_BRANCH"),
        version=os.getenv("INPUT_VERSION"),
        commit_sha=os.getenv("INPUT_COMMIT_SHA")
    )
