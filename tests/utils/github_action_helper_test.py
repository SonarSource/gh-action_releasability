import os
import tempfile
import unittest

from utils.github_action_helper import GithubActionHelper


class GithubActionHelperTest(unittest.TestCase):
    def test_set_output(self):
        with tempfile.NamedTemporaryFile(suffix="", prefix=os.path.basename(__file__)) as temp_file:
            os.environ['GITHUB_OUTPUT'] = temp_file.name

            GithubActionHelper.set_output('function', 'output')

            assert temp_file.read().decode("utf-8").strip() == "function=output"

    def test_set_multiline_output(self):
        with tempfile.NamedTemporaryFile(suffix="", prefix=os.path.basename(__file__)) as temp_file:
            os.environ['GITHUB_OUTPUT'] = temp_file.name

            output = "some great \n text"

            GithubActionHelper.set_multiline_output('multiple-lines', output)

            assert temp_file.read().decode("utf-8").strip() == "multiple-lines<<EOF\nsome great \n text\nEOF"
