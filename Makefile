SHELL := /bin/bash

test:
	pipenv install --dev
	pipenv run pytest

releasability-check:
	pipenv install
	pipenv run releasability_check
