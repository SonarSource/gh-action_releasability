import re
import sys
import traceback

from release.utils.release import revoke_release, publish_all_artifacts_to_binaries
from release.steps.ReleaseRequest import ReleaseRequest
from release.utils.artifactory import Artifactory
from release.utils.binaries import Binaries
from release.utils.burgr import Burgr
from release.utils.github import GitHub
from slack_sdk.errors import SlackApiError
from release.vars import githup_api_url, github_token, github_event_path, burgrx_url, burgrx_user, burgrx_password, \
    artifactory_apikey, publish_to_binaries, slack_client, slack_channel, binaries_bucket_name


def set_output(function, output):
    print(f"::set-output name={function}::{output}")


def notify_slack(msg):
    if slack_channel is not None:
        try:
            return slack_client.chat_postMessage(
                    channel=slack_channel,
                    text=msg)
        except SlackApiError as e:
            print(f"Could not notify slack: {e.response['error']}")


def abort_release(github: GitHub, artifactory: Artifactory, binaries: Binaries, rr: ReleaseRequest):
    print(f"::error  Aborting release")
    github.revoke_release()
    revoke_release(artifactory, binaries, rr)
    set_output("release", f"{rr.project}:{rr.buildnumber} revoked")
    sys.exit(1)


def main():
    github = GitHub(githup_api_url, github_token, github_event_path)
    repo = github.get_repo()
    ref = github.get_ref()

    organisation, project = repo.split("/")
    version = ref.replace('refs/tags/', '', 1)

    # tag shall be like X.X.X.BUILD_NUMBER or X.X.X-MX.BUILD_NUMBER or X.X.X+BUILD_NUMBER (SEMVER)
    version_pattern = re.compile(r'^\d+\.\d+\.\d+(?:-M\d+)?[.+](\d+)$')
    version_match = version_pattern.match(version)
    if version_match is None:
        print(f"::error Found wrong version: {version}")
        sys.exit(1)

    build_number = version_match.groups()[0]


    release_info = github.release_info(version)
    if not release_info:
        print(f"::error  No release info found")
        sys.exit(1)

    rr = ReleaseRequest(organisation, project, build_number, github.current_branch(), github.get_sha())
    burgr = Burgr(burgrx_url, burgrx_user, burgrx_password, rr)

    try:
        burgr.start_releasability_checks(version)
        burgr.get_releasability_status(version)
    except Exception as e:
        print(f"::error releasability did not complete correctly. " + str(e))
        github.revoke_release()
        sys.exit(1)
    set_output("releasability", f"{repo}:{version} releasability DONE")

    artifactory = Artifactory(artifactory_apikey)
    buildinfo = artifactory.receive_build_info(rr)
    binaries = None

    try:
        artifactory.promote(rr, buildinfo)
        set_output("promote", f"{repo}:{version} promote DONE")

        if publish_to_binaries:
            binaries = Binaries(binaries_bucket_name)
            publish_all_artifacts_to_binaries(artifactory, binaries, rr, buildinfo)
            set_output("publish_to_binaries", f"{repo}:{version} publish_to_binaries DONE")

        burgr.notify('passed')
        notify_slack(f"Successfully released {repo}:{version}")

    except Exception as e:
        error = f"::error release {repo}:{version} did not complete correctly: {repr(e)}"
        print(error)
        print(traceback.format_exc())
        notify_slack(error)
        abort_release(github, artifactory, binaries, rr)
        sys.exit(1)


if __name__ == "__main__":
    main()