#!/usr/bin/env bash
# Runnable walkthrough of pycliphist. Uses a throwaway database so your real
# clipboard history is never touched. Run from the repository root:
#   bash examples/demo.sh
set -euo pipefail
export PYTHONPATH="${PYTHONPATH:-}:src"
export PYCLIPHIST_DB="$(mktemp -u).db"
PYTHON="${PYTHON:-python3}"

run() { echo "\$ pycliphist $*"; "$PYTHON" -m pycliphist "$@"; echo; }

run add "SELECT * FROM users;"
run add "https://example.com/docs"
run list
run search users
run get 2 --raw
run stats
run delete 2
run clear --yes

rm -f "$PYCLIPHIST_DB"
