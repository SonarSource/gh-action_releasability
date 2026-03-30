SHELL := /bin/bash

test:
	pipenv install --dev --deploy
	pipenv run pytest

releasability-check:
	pipenv install --deploy
	pipenv run releasability_check
