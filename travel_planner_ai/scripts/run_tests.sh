#!/bin/bash

# Change to the project root directory
cd "$(dirname "$0")/.."

# Run pytest with verbose output
echo "Running backend tests..."
python -m pytest travel_planner_ai/backend/tests/ -v

# Check if tests passed
if [ $? -eq 0 ]; then
    echo "All tests passed!"
else
    echo "Some tests failed. Please check the output above."
fi 