import os
import tempfile
import unittest
from unittest.mock import patch

import main
from main import do_releasability_checks
from releasability.releasability_check_result import ReleasabilityCheckResult
from releasability.releasability_checks_report import ReleasabilityChecksReport
from releasability.releasability_service import ReleasabilityService
from utils.github_action_helper import GithubActionHelper


class MainTest(unittest.TestCase):

    def setUp(self) -> None:
        main.WAIT_TIME_AFTER_TRIGGER_RELEASABILITY_CHECKS_IN_SECONDS = 0

    def test_do_releasability_checks_should_define_output_logs_given_it_performed_well(self):
        correlation_id = "fake-correlation-id"
        with tempfile.NamedTemporaryFile(suffix="", prefix=os.path.basename(__file__)) as temp_file:
            os.environ['GITHUB_OUTPUT'] = temp_file.name
            with patch.object(ReleasabilityService, '__init__', return_value=None):
                with patch.object(ReleasabilityService, 'start_releasability_checks', return_value=correlation_id):
                    report = ReleasabilityChecksReport([
                        ReleasabilityCheckResult("check name", ReleasabilityCheckResult.CHECK_PASSED, "it works"),
                    ])
                    with patch.object(ReleasabilityService, 'get_releasability_report', return_value=report):
                        organization = "some-org"
                        repository = "some-repo"
                        branch = "some-branch"
                        version = "4.3.2.1"
                        commit_sha = "ef1232ad12321"

                        with patch.object(GithubActionHelper,'set_output_logs') as mock_set_output_logs:
                            with patch.object(GithubActionHelper, 'set_output_status') as mock_set_output_status:

                                do_releasability_checks(organization, repository, branch, version, commit_sha)

                                mock_set_output_logs.assert_called_once_with("✅ check name  - it works")

    def test_do_releasability_checks_should_define_output_logs_given_it_did_not_perform_well(self):
        correlation_id = "fake-correlation-id"

        with tempfile.NamedTemporaryFile(suffix="", prefix=os.path.basename(__file__)) as temp_file:
            os.environ['GITHUB_OUTPUT'] = temp_file.name
            with patch.object(ReleasabilityService, '__init__', return_value=None):
                with patch.object(ReleasabilityService, 'start_releasability_checks', return_value=correlation_id):
                    report = ReleasabilityChecksReport([
                        ReleasabilityCheckResult("check name", ReleasabilityCheckResult.CHECK_FAILED, "it failed"),
                    ])
                    with patch.object(ReleasabilityService, 'get_releasability_report', return_value=report):
                        organization = "some-org"
                        repository = "some-repo"
                        branch = "some-branch"
                        version = "4.3.2.1"
                        commit_sha = "ef1232ad12321"

                        with patch.object(GithubActionHelper,'set_output_logs') as mock_set_output_logs:
                            with patch.object(GithubActionHelper, 'set_output_status') as mock_set_output_status:

                                do_releasability_checks(organization, repository, branch, version, commit_sha)

                                mock_set_output_logs.assert_called_once_with("❌ check name  - it failed")
    def test_do_releasability_checks_should_define_output_status_as_success_given_it_performed_well(self):
        correlation_id = "fake-correlation-id"

        with patch.object(ReleasabilityService, '__init__', return_value=None):
            with patch.object(ReleasabilityService, 'start_releasability_checks', return_value=correlation_id):
                report = ReleasabilityChecksReport([
                    ReleasabilityCheckResult("check name", ReleasabilityCheckResult.CHECK_PASSED, "it works"),
                ])
                with patch.object(ReleasabilityService, 'get_releasability_report', return_value=report):
                    organization = "some-org"
                    repository = "some-repo"
                    branch = "some-branch"
                    version = "4.3.2.1"
                    commit_sha = "ef1232ad12321"

                    with patch.object(GithubActionHelper,'set_output_logs') as mock_set_output_logs:
                        with patch.object(GithubActionHelper, 'set_output_status') as mock_set_output_status:

                            do_releasability_checks(organization, repository, branch, version, commit_sha)

                            mock_set_output_status.assert_called_once_with("0")

    def test_do_releasability_checks_should_define_output_status_as_error_given_it_did_not_perform_well(self):
        correlation_id = "fake-correlation-id"

        with patch.object(ReleasabilityService, '__init__', return_value=None):
            with patch.object(ReleasabilityService, 'start_releasability_checks', return_value=correlation_id):
                report = ReleasabilityChecksReport([
                    ReleasabilityCheckResult("check name", ReleasabilityCheckResult.CHECK_FAILED, "it didn't work"),
                ])
                with patch.object(ReleasabilityService, 'get_releasability_report', return_value=report):
                    organization = "some-org"
                    repository = "some-repo"
                    branch = "some-branch"
                    version = "4.3.2.1"
                    commit_sha = "ef1232ad12321"

                    with patch.object(GithubActionHelper,'set_output_logs') as mock_set_output_logs:
                        with patch.object(GithubActionHelper, 'set_output_status') as mock_set_output_status:

                            do_releasability_checks(organization, repository, branch, version, commit_sha)

                            mock_set_output_status.assert_called_once_with("1")
