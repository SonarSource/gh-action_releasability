import os
import sys
import time

from releasability.releasability_service import ReleasabilityService
from utils.github_action_helper import GithubActionHelper

WAIT_TIME_AFTER_TRIGGER_RELEASABILITY_CHECKS_IN_SECONDS = 20


def do_releasability_checks(organization: str, repository: str, branch: str, version: str, commit_sha: str):
    try:
        releasability = ReleasabilityService()
        correlation_id = releasability.start_releasability_checks(
            organization,
            repository,
            branch,
            version,
            commit_sha
        )

        time.sleep(WAIT_TIME_AFTER_TRIGGER_RELEASABILITY_CHECKS_IN_SECONDS)  # no need to fetch directly it takes anyway some
        # time for the checks to perform

        report = releasability.get_releasability_report(correlation_id)
        GithubActionHelper.set_output_logs(str(report))

        if report.contains_error():
            print("::error::Releasability checks failed")
            GithubActionHelper.set_output_status("1")
        else:
            print("::notice::Releasability checks passed successfully")
            GithubActionHelper.set_output_status("0")

    except Exception as ex:
        print(f"::error:: {ex}")
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
