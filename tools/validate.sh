#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

echo "==> python3 -m unittest discover -s tools/tests"
python3 -m unittest discover -s tools/tests -p "test_*.py"

echo "==> claude plugin validate . --strict"
claude plugin validate . --strict

echo "==> python3 tools/checks.py"
python3 tools/checks.py

echo "==> all checks passed"
