#!/bin/bash
set -ex
poetry run python3 -m uvicorn src.activities.local_test:local_app --reload --host 0.0.0.0 --port ${PORT:-3000} --limit-max-requests 5000 --timeout-keep-alive 1200

