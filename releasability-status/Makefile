SHELL := /bin/bash

test:
	pipenv install --dev --deploy
	pipenv run pytest

releasability-status:
	pipenv install --deploy
	pipenv run releasability-status
