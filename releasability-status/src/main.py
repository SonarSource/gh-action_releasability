import os
import json
from github_action_utils import set_output

GITHUB_ACTION_OUTPUT_STATUS_NAME = "status"
GITHUB_ACTION_OUTPUT_STATE_NAME = "state"
GITHUB_ACTION_OUTPUT_MESSAGE_NAME = "message"
STATE_SUCCESS = "success"
STATE_FAILURE = "failure"

def find_failed_checks(result:dict):
    failed = []
    for key in result:
        if key.startswith('releasability') and result[key] not in ["PASSED", "NOT_RELEVANT"]:
            failed.append(key.lstrip('releasability'))
    return failed

def parse_releasability_output(version:str, releasability_check_result:dict, optional_checks:list[str]):
    if releasability_check_result["status"] == "0":
        set_output(GITHUB_ACTION_OUTPUT_STATUS_NAME, releasability_check_result["status"])
        set_output(GITHUB_ACTION_OUTPUT_STATE_NAME, STATE_SUCCESS)
        set_output(GITHUB_ACTION_OUTPUT_MESSAGE_NAME, f"✈ {version} passed releasability checks")
        return

    failed = find_failed_checks(releasability_check_result)
    failed_checks = ",".join(failed)
    print('failed checks:',failed)

    if set(failed).issubset(optional_checks):
        set_output(GITHUB_ACTION_OUTPUT_STATUS_NAME, "0")
        set_output(GITHUB_ACTION_OUTPUT_STATE_NAME, STATE_SUCCESS)
        set_output(GITHUB_ACTION_OUTPUT_MESSAGE_NAME, f"✈ {version} failed optional checks -> {failed_checks}")
        return

    set_output(GITHUB_ACTION_OUTPUT_STATUS_NAME, releasability_check_result["status"])
    set_output(GITHUB_ACTION_OUTPUT_STATE_NAME, STATE_FAILURE)
    set_output(GITHUB_ACTION_OUTPUT_MESSAGE_NAME, f"✈ {version} failed checks -> {failed_checks}")

if __name__ == "__main__":
    version=os.getenv("INPUT_VERSION", "")
    releasability_check_result_str=os.getenv("RELEASABILITY_CHECK_RESULT", "")
    optional_checks_str=os.getenv("OPTIONAL_CHECKS", "")
    optional_checks = optional_checks_str.split(",") if optional_checks_str != "" else []

    if version == "" or releasability_check_result_str == "":
        set_output(GITHUB_ACTION_OUTPUT_STATUS_NAME, "1")
        set_output(GITHUB_ACTION_OUTPUT_STATE_NAME, STATE_FAILURE)
        set_output(GITHUB_ACTION_OUTPUT_MESSAGE_NAME, "Releasability checks failed, check logs for more details")
        exit(1)

    releasability_check_result = json.loads(releasability_check_result_str)

    parse_releasability_output(
        version=version,
        releasability_check_result=releasability_check_result,
        optional_checks=optional_checks,
    )
