import copy
import json
import time
import uuid

import boto3

from releasability.releasability_check_result import ReleasabilityCheckResult
from releasability.releasability_checks_report import ReleasabilityChecksReport
from releasability.vars import releasability_aws_region
from utils.timeout import has_exceeded_timeout
from utils.version_helper import VersionHelper


class ReleasabilityException(Exception):
    pass


class CouldNotRetrieveReleasabilityCheckResultsException(ReleasabilityException):
    pass


class ReleasabilityService:
    FETCH_CHECK_RESULT_TIMEOUT_SECONDS = 60 * 10
    SQS_MAX_POLLED_MESSAGES_AT_A_TIME = 10
    SQS_POLL_WAIT_TIME = 20
    SQS_VISIBILITY_TIMEOUT = 0  # Allows other consumers to read messages

    ARN_SNS = 'arn:aws:sns'
    ARN_SQS = 'arn:aws:sqs'

    # Make sure to update the outputs in action.yml if this list changes
    EXPECTED_RELEASABILITY_CHECK_NAMES = {
        "CheckDependencies",
        "QA",
        "Jira",
        "WhiteSource",
        "CheckPeacheeLanguagesStatistics",
        "QualityGate",
        "ParentPOM",
        "GitHub",
        "CheckManifestValues",
    }

    ACK_TYPE = "ACK"

    session: boto3.Session

    def __init__(self):
        self.session = boto3.Session(region_name=releasability_aws_region)
        account_id = self._get_aws_account_id()
        self._define_arn_constants(releasability_aws_region, account_id)

    def _get_aws_account_id(self) -> str:
        return boto3.client('sts').get_caller_identity().get('Account')

    def _define_arn_constants(self, aws_region: str, aws_account_id: str):
        self.TRIGGER_TOPIC_ARN = f"{ReleasabilityService.ARN_SNS}:{aws_region}:{aws_account_id}:ReleasabilityTriggerTopic"
        self.RESULT_TOPIC_ARN = f"{ReleasabilityService.ARN_SNS}:{aws_region}:{aws_account_id}:ReleasabilityResultTopic"
        self.RESULT_QUEUE_ARN = f"{ReleasabilityService.ARN_SQS}:{aws_region}:{aws_account_id}:ReleasabilityResultQueue"

    def start_releasability_checks(self, organization: str, repository: str, branch: str, version: str, commit_sha: str):
        VersionHelper.validate_version(version)

        print(f"Starting releasability check: {organization}/{repository}#{version}@{commit_sha}")

        correlation_id = str(uuid.uuid4())
        sns_request = self._build_sns_request(
            correlation_id=correlation_id,
            organization=organization,
            project_name=repository,
            branch_name=branch,
            version=version,
            revision=commit_sha,
        )

        response = self.session.client("sns").publish(
            TopicArn=self.TRIGGER_TOPIC_ARN,
            Message=str(sns_request),
        )
        print(f"Issued SNS message {response['MessageId']}; the request identifier is {correlation_id}")
        return correlation_id

    def _build_sns_request(
        self,
        correlation_id: str,
        organization: str,
        project_name: str,
        branch_name: str,
        revision: str,
        version: str,
    ):

        build_number = VersionHelper.extract_build_number(version)

        sns_request = {
            'uuid': correlation_id,
            'responseToARN': self.RESULT_TOPIC_ARN,
            'repoSlug': f'{organization}/{project_name}',
            'version': version,
            'vcsRevision': revision,
            'artifactoryBuildNumber': build_number,
            'branchName': branch_name,
        }
        return sns_request

    @staticmethod
    def _arn_to_sqs_url(arn):
        parts = arn.split(':')
        service = parts[2]

        if service != "sqs":
            raise ValueError(f"Invalid sqs ARN: {arn}")

        region = parts[3]
        account_number = parts[4]
        queue_name = parts[5]
        return f'https://sqs.{region}.amazonaws.com/{account_number}/{queue_name}'

    def get_releasability_report(self, correlation_id: str) -> ReleasabilityChecksReport:

        check_results = self._get_check_results(correlation_id)
        return ReleasabilityChecksReport(check_results)

    def _get_check_results(self, correlation_id: str):
        checks_awaiting_result = copy.deepcopy(self._get_checks())
        received_check_results = list[ReleasabilityCheckResult]()

        now = time.time()
        while len(checks_awaiting_result) > 0 and not has_exceeded_timeout(now, ReleasabilityService.FETCH_CHECK_RESULT_TIMEOUT_SECONDS):
            filtered_messages = self._fetch_filtered_check_results(correlation_id)
            for message_payload in filtered_messages:
                check_name = message_payload["checkName"]

                if check_name in checks_awaiting_result:
                    print(f' received: {message_payload}')
                    received_check_results.append(
                        ReleasabilityCheckResult(
                            message_payload["checkName"],
                            message_payload["type"],
                            message_payload["message"] if "message" in message_payload else None,
                        )
                    )
                    checks_awaiting_result.remove(check_name)

        if len(checks_awaiting_result) == 0:
            return received_check_results
        else:
            raise CouldNotRetrieveReleasabilityCheckResultsException(
                f'Received {len(received_check_results)}/{self._get_checks_count()} check result(s) messages within '
                f'allowed time ({ReleasabilityService.FETCH_CHECK_RESULT_TIMEOUT_SECONDS} seconds) '
                f'(no results received for check(s): {",".join(checks_awaiting_result)})'
            )

    @staticmethod
    def match_correlation_id(msg, correlation_id):
        return msg['requestUUID'] == correlation_id

    @staticmethod
    def not_an_ack_message(msg):
        return msg['type'] != ReleasabilityService.ACK_TYPE

    def _fetch_filtered_check_results(self, correlation_id) -> list:
        unfiltered_messages = self._fetch_check_results()
        current_messages = list(filter(lambda msg: self.match_correlation_id(msg, correlation_id), unfiltered_messages))
        self._delete_messages(current_messages)
        relevant_messages = list(filter(self.not_an_ack_message, current_messages))
        return relevant_messages

    def _delete_messages(self, messages: list):
        sqs_client = self.session.client('sqs')
        sqs_queue_url = self._arn_to_sqs_url(self.RESULT_QUEUE_ARN)
        for message in messages:
            sqs_client.delete_message(QueueUrl=sqs_queue_url, ReceiptHandle=message['ReceiptHandle'])

    def _fetch_check_results(self) -> list:

        sqs_client = self.session.client('sqs')
        sqs_queue_url = self._arn_to_sqs_url(self.RESULT_QUEUE_ARN)

        sqs_queue_messages = sqs_client.receive_message(
            QueueUrl=sqs_queue_url,
            MaxNumberOfMessages=ReleasabilityService.SQS_MAX_POLLED_MESSAGES_AT_A_TIME,
            WaitTimeSeconds=ReleasabilityService.SQS_POLL_WAIT_TIME,
            VisibilityTimeout=ReleasabilityService.SQS_VISIBILITY_TIMEOUT,
        )

        result = []

        if "Messages" in sqs_queue_messages:
            for json_message in sqs_queue_messages['Messages']:
                body = json.loads(json_message['Body'])
                content = json.loads(body['Message'])
                content['ReceiptHandle'] = json_message['ReceiptHandle']
                result.append(content)
        return result

    def _get_checks(self) -> set[str]:
        return ReleasabilityService.EXPECTED_RELEASABILITY_CHECK_NAMES

    def _get_checks_count(self):
        return len(self._get_checks())
