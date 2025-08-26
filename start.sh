#!/bin/bash
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$PROJECT_DIR/venv/bin/activate"
exec gunicorn --workers 3 --timeout 300 --bind 127.0.0.1:8102 --chdir "$PROJECT_DIR" run:app

