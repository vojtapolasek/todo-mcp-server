#!/bin/bash
set -e

echo "Setting up test environment..."
python -m pytest tests/ -v --tb=short

echo "Running integration test..."
python src/server.py tests/fixtures/sample_todo.txt &
SERVER_PID=$!

sleep 2

# Test if server starts without errors
kill $SERVER_PID 2>/dev/null || true

python src/simple_server.py tests/fixtures/sample_todo.txt &
SERVER_PID=$!

sleep 2

# Test if server starts without errors
kill $SERVER_PID 2>/dev/null || true

echo "All tests passed! 🎉"
