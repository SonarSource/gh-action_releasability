# Releasability Checks Architecture

## Overview

This document describes the architecture for the GitHub Action Releasability system, including both the current
lambda-based implementation and the proposed hybrid approach that supports inline checks alongside existing
lambda-based checks.

## Current Architecture (Lambda-Based)

### Components

1. **GitHub Action** (`action.yml`)
   - Entry point for the releasability checks
   - Validates inputs and triggers the Python application
   - Handles outputs and status reporting

2. **Python Application** (`src/main.py`)
   - Main orchestrator that coordinates the releasability checks
   - Manages AWS credentials and service initialization
   - Processes results and sets GitHub Action outputs

3. **ReleasabilityService** (`src/releasability/releasability_service.py`)
   - Core service that manages the check lifecycle
   - Publishes SNS messages to trigger lambda functions
   - Polls SQS for results from lambda functions
   - Handles correlation IDs for request tracking

4. **AWS Infrastructure**
   - **SNS Topic** (`ReleasabilityTriggerTopic`): Receives check requests
   - **Lambda Functions**: Execute individual releasability checks
   - **SNS Topic** (`ReleasabilityResultTopic`): Receives check results
   - **SQS Queue** (`ReleasabilityResultQueue`): Buffers results for polling

5. **Check Results** (`src/releasability/releasability_check_result.py`)
   - Data structure representing individual check results
   - Supports states: PASSED, NOT_RELEVANT, ERROR, FAILED

6. **Report Generation** (`src/releasability/releasability_checks_report.py`)
   - Aggregates multiple check results
   - Provides summary and error detection

### Current Check Types

The system currently supports 9 lambda-based checks:

- CheckDependencies
- QA
- Jira
- CheckPeacheeLanguagesStatistics
- QualityGate
- ParentPOM
- GitHub
- CheckManifestValues

## Proposed Hybrid Architecture

### Design Goals

1. **Backward Compatibility**: Maintain existing lambda-based checks without modification
2. **Performance**: Reduce latency for new checks by executing them inline
3. **Simplicity**: Eliminate AWS infrastructure dependencies for new checks
4. **Consistency**: Maintain unified result format and reporting
5. **Extensibility**: Easy addition of new inline checks

### Architecture Components

#### 1. Enhanced ReleasabilityService

The `ReleasabilityService` will be extended to support both execution modes:

```python
class ReleasabilityService:
    def __init__(self):
        # Existing lambda infrastructure
        self.lambda_checks = {...}
        # New inline check registry
        self.inline_checks = {...}

    def start_releasability_checks(self, ...):
        # Execute inline checks immediately
        inline_results = self._execute_inline_checks(...)
        # Trigger lambda checks as before
        correlation_id = self._trigger_lambda_checks(...)
        return correlation_id, inline_results

    def get_releasability_report(self, correlation_id, inline_results):
        # Combine inline and lambda results
        lambda_results = self._get_lambda_check_results(correlation_id)
        all_results = inline_results + lambda_results
        return ReleasabilityChecksReport(all_results)
```

#### 2. Inline Check Framework

New abstract base class for inline checks:

```python
from abc import ABC, abstractmethod

class InlineCheck(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def execute(self, context: CheckContext) -> ReleasabilityCheckResult:
        pass

class CheckContext:
    def __init__(self, organization: str, repository: str,
                 branch: str, version: str, commit_sha: str):
        self.organization = organization
        self.repository = repository
        self.branch = branch
        self.version = version
        self.commit_sha = commit_sha
```

#### 3. Check Registry

Centralized registry for managing both check types:

```python
class CheckRegistry:
    def __init__(self):
        self.lambda_checks = set(ReleasabilityService.EXPECTED_RELEASABILITY_CHECK_NAMES)
        self.inline_checks = {}

    def register_inline_check(self, check: InlineCheck):
        self.inline_checks[check.name] = check

    def get_all_check_names(self):
        return self.lambda_checks | set(self.inline_checks.keys())
```

#### 4. Enhanced Main Application

The main application will be updated to handle the hybrid approach:

```python
def do_releasability_checks(organization: str, repository: str,
                           branch: str, version: str, commit_sha: str):
    try:
        releasability = ReleasabilityService()

        # Execute inline checks immediately
        inline_results = releasability.execute_inline_checks(
            organization, repository, branch, version, commit_sha
        )

        # Trigger lambda checks
        correlation_id = releasability.start_lambda_checks(
            organization, repository, branch, version, commit_sha
        )

        # Get combined report
        report = releasability.get_combined_report(correlation_id, inline_results)

        # Process results as before
        GithubActionHelper.set_output_logs(str(report))
        for check in report.get_checks():
            name = f'releasability{check.name}'
            set_output(name, check.state)

        # Status handling remains the same
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
```

### Data Flow

#### Inline Check Execution Flow

1. **GitHub Action** triggers the Python application
2. **Main Application** initializes ReleasabilityService
3. **ReleasabilityService** executes inline checks immediately:
   - Creates CheckContext with repository information
   - Iterates through registered inline checks
   - Each check executes and returns ReleasabilityCheckResult
   - Results are collected and returned
4. **ReleasabilityService** triggers lambda checks via SNS
5. **Main Application** waits for lambda results via SQS polling
6. **ReleasabilityService** combines inline and lambda results
7. **Main Application** processes combined results and sets outputs

#### Result Aggregation

The system maintains a unified result format:

```python
class ReleasabilityChecksReport:
    def __init__(self, lambda_results: List[ReleasabilityCheckResult],
                 inline_results: List[ReleasabilityCheckResult]):
        self.__checks = lambda_results + inline_results

    def get_checks(self) -> List[ReleasabilityCheckResult]:
        return self.__checks

    def contains_error(self) -> bool:
        return any(not check.passed for check in self.__checks)
```

### Benefits of Hybrid Approach

1. **Performance**: Inline checks execute immediately without AWS round-trips
2. **Reliability**: Reduced dependency on AWS infrastructure for new checks
3. **Cost**: Lower AWS costs for inline checks (no lambda invocations)
4. **Development Speed**: Faster iteration and testing of new checks
5. **Backward Compatibility**: Existing lambda checks continue to work unchanged
6. **Unified Interface**: Both check types use the same result format and reporting

### Migration Strategy

1. **Phase 1**: Implement inline check framework alongside existing lambda system
2. **Phase 2**: Migrate simple checks from lambda to inline (e.g., CheckManifestValues)
3. **Phase 3**: Add new checks as inline checks by default
4. **Phase 4**: Gradually migrate remaining lambda checks based on complexity and requirements

### Configuration

Inline checks can be configured via environment variables or configuration files:

```python
# Environment variable example
INLINE_CHECKS_ENABLED=true
INLINE_CHECK_TIMEOUT=30  # seconds

# Configuration file example
{
  "inline_checks": {
    "enabled": true,
    "timeout": 30,
    "checks": ["CheckManifestValues", "NewCustomCheck"]
  }
}
```

### Error Handling

The system maintains robust error handling for both check types:

- **Inline Check Errors**: Caught and wrapped in ReleasabilityCheckResult with ERROR state
- **Lambda Check Errors**: Handled by existing timeout and retry mechanisms
- **Mixed Results**: System continues processing even if some checks fail
- **Timeout Handling**: Inline checks have configurable timeouts to prevent hanging

### Monitoring and Observability

Enhanced logging and monitoring for the hybrid system:

```python
import logging

logger = logging.getLogger(__name__)

class ReleasabilityService:
    def execute_inline_checks(self, ...):
        logger.info(f"Executing {len(self.inline_checks)} inline checks")
        start_time = time.time()

        for check_name, check in self.inline_checks.items():
            try:
                logger.debug(f"Executing inline check: {check_name}")
                result = check.execute(context)
                logger.info(f"Inline check {check_name}: {result.state}")
            except Exception as e:
                logger.error(f"Inline check {check_name} failed: {e}")
                result = ReleasabilityCheckResult(check_name, "ERROR", str(e))

            results.append(result)

        duration = time.time() - start_time
        logger.info(f"Inline checks completed in {duration:.2f}s")
        return results
```

This hybrid architecture provides a smooth transition path from the current lambda-based system while enabling
faster, more cost-effective inline checks for new functionality.
