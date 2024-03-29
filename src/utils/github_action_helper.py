import os
import uuid

GITHUB_ACTION_OUTPUT_LOG_NAME = "logs"
GITHUB_ACTION_OUTPUT_STATUS_NAME = "status"
GITHUB_OUTPUT_ENVIRONMENT_NAME = "GITHUB_OUTPUT"


class GithubActionHelper:

    @staticmethod
    def set_output(output_name, value):
        """Sets the GitHub Action output.

        Keyword arguments:
        output_name - The name of the output
        value - The value of the output
        """
        if GITHUB_OUTPUT_ENVIRONMENT_NAME in os.environ:
            with open(os.environ[GITHUB_OUTPUT_ENVIRONMENT_NAME], "a") as output_stream:
                print(f"{output_name}={value}", file=output_stream)

    @staticmethod
    def set_multiline_output(output_name, value):
        """Sets the GitHub Action output for multiple lines

        Keyword arguments:
        output_name - The name of the output
        value - The value of the output
        """
        if GITHUB_OUTPUT_ENVIRONMENT_NAME in os.environ:
            with open(os.environ[GITHUB_OUTPUT_ENVIRONMENT_NAME], "a") as output_stream:
                delimiter = 'EOF'
                print(f'{output_name}<<{delimiter}', file=output_stream)
                print(value, file=output_stream)
                print(delimiter, file=output_stream)

    @staticmethod
    def set_output_logs(logs):
        GithubActionHelper.set_multiline_output(GITHUB_ACTION_OUTPUT_LOG_NAME, logs)

    @staticmethod
    def set_output_status(status):
        GithubActionHelper.set_output(GITHUB_ACTION_OUTPUT_STATUS_NAME, status)
