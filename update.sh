#!/bin/bash
# this script will replace backend/frontend with newly cloned ones

set -e

BACKEND_DIR="backend"
FRONTEND_DIR="frontend"
REPO_URL="https://github.com/qonyx1/scambanner.git"
TEMP_DIR="temp_repo"

rm -rf "./$BACKEND_DIR" "./$FRONTEND_DIR"
git clone "$REPO_URL" "$TEMP_DIR"

mv "$TEMP_DIR/$BACKEND_DIR" .
mv "$TEMP_DIR/$FRONTEND_DIR" .

rm -rf "$TEMP_DIR"