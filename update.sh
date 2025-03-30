#!/bin/bash

set -e

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

if [ ! -d "$VENV_DIR" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "Failed to activate virtual environment."
    exit 1
fi

"$PYTHON_INTERPRETER" -m pip install -r "./requirements.txt"

pm2 delete scambanner_backend || true  
pm2 delete scambanner_frontend || true  

cd "$BACKEND_DIR"
pm2 start main.py --name scambanner_backend --interpreter "$PYTHON_INTERPRETER" --namespace scambanner
cd ..

cd "$FRONTEND_DIR"
pm2 start main.py --name scambanner_frontend --interpreter "$PYTHON_INTERPRETER" --namespace scambanner
cd ..

echo "Backend and frontend started successfully."
