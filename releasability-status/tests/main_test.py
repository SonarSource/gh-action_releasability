from main import find_failed_checks, parse_releasability_output
import tempfile
import os

def test_find_failed_checks():
    result = {
        "releasabilityParentPOM": "NOT_RELEVANT",
        "releasabilityGitHub": "NOT_RELEVANT",
        "releasabilityCheckDependencies": "PASSED",
        "releasabilityQualityGate": "PASSED",
        "releasabilityCheckPeacheeLanguagesStatistics": "NOT_RELEVANT",
        "releasabilityQA": "ERROR",
        "releasabilityJira": "FAILED",
        "releasabilityCheckManifestValues": "PASSED",
        "status": "1"
    }
    failed = find_failed_checks(result)
    assert failed == ['QA', 'Jira']

def test_parse_releasability_output_failed():
    result = {
        "releasabilityParentPOM": "NOT_RELEVANT",
        "releasabilityGitHub": "NOT_RELEVANT",
        "releasabilityCheckDependencies": "PASSED",
        "releasabilityQualityGate": "PASSED",
        "releasabilityCheckPeacheeLanguagesStatistics": "NOT_RELEVANT",
        "releasabilityQA": "ERROR",
        "releasabilityJira": "FAILED",
        "releasabilityCheckManifestValues": "PASSED",
        "status": "1"
    }
    temp = tempfile.mktemp()
    os.environ['GITHUB_OUTPUT'] = temp
    parse_releasability_output('1.0', result, [])
    with open(temp) as f:
        out = f.read().split("\n")
        assert out[4] == "failure"
        assert out[7] == "✈ 1.0 failed checks -> QA,Jira"
    os.remove(temp)

def test_parse_releasability_output_success():
    result = {
        "releasabilityParentPOM": "NOT_RELEVANT",
        "releasabilityGitHub": "NOT_RELEVANT",
        "releasabilityCheckDependencies": "PASSED",
        "releasabilityQualityGate": "PASSED",
        "releasabilityCheckPeacheeLanguagesStatistics": "NOT_RELEVANT",
        "releasabilityQA": "PASSED",
        "releasabilityJira": "PASSED",
        "releasabilityCheckManifestValues": "PASSED",
        "status": "0"
    }
    temp = tempfile.mktemp()
    os.environ['GITHUB_OUTPUT'] = temp
    parse_releasability_output('1.0', result, [])
    with open(temp) as f:
        out = f.read().split("\n")
        assert out[4] == "success"
        assert out[7] == "✈ 1.0 passed releasability checks"
    os.remove(temp)

def test_parse_releasability_output_optional():
    result = {
        "releasabilityParentPOM": "NOT_RELEVANT",
        "releasabilityGitHub": "NOT_RELEVANT",
        "releasabilityCheckDependencies": "PASSED",
        "releasabilityQualityGate": "PASSED",
        "releasabilityCheckPeacheeLanguagesStatistics": "NOT_RELEVANT",
        "releasabilityQA": "FAILED",
        "releasabilityJira": "FAILED",
        "releasabilityCheckManifestValues": "PASSED",
        "status": "1"
    }
    temp = tempfile.mktemp()
    os.environ['GITHUB_OUTPUT'] = temp
    parse_releasability_output('1.0', result, ["Jira", "QA"])
    with open(temp) as f:
        out = f.read().split("\n")
        assert out[4] == "success"
        assert out[7] == "✈ 1.0 failed optional checks -> QA,Jira"
    os.remove(temp)
