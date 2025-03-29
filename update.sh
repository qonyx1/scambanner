#!/bin/bash
# this script will replace backend/frontend with newly cloned ones

set -e

BACKEND_DIR="backend"
FRONTEND_DIR="frontend"
REPO_URL="https://github.com/qonyx1/scambanner.git"
TEMP_DIR="temp_repo"

sleep 2
rm -rf "./$BACKEND_DIR" "./$FRONTEND_DIR"

sleep 2
git clone "$REPO_URL" "$TEMP_DIR"

sleep 2
mv "$TEMP_DIR/$BACKEND_DIR" .

sleep 2
mv "$TEMP_DIR/$FRONTEND_DIR" .

sleep 2
rm -rf "$TEMP_DIR"