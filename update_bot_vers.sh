#!/bin/bash
# Updates but does not run/restart the program.

set -e
cd ..
BACKEND_DIR="backend"
FRONTEND_DIR="frontend"
REPO_URL="https://github.com/qonyx1/scambanner.git"
TEMP_DIR="temp_repo"
VENV_DIR="$(realpath .venv)"
PYTHON_INTERPRETER="$VENV_DIR/bin/python3"

rm -rf "$BACKEND_DIR" "$FRONTEND_DIR"

git clone "$REPO_URL" "$TEMP_DIR"
mv "$TEMP_DIR/$BACKEND_DIR" .
mv "$TEMP_DIR/$FRONTEND_DIR" .
rm -rf "$TEMP_DIR"