#!/bin/bash

# Change to the project root directory
cd "$(dirname "$0")"

# Activate poetry environment if using poetry
if command -v poetry &>/dev/null; then
    echo "Running tests with Poetry..."
    poetry run pytest "$@"
else
    echo "Poetry not found, running with system Python..."
    python -m pytest "$@"
fi

# Example usage:
# ./run_tests.sh                     # Run all tests
# ./run_tests.sh tests/test_trips_router.py  # Run specific test file
# ./run_tests.sh -m unit             # Run only unit tests
# ./run_tests.sh -v                  # Verbose output 