#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Function to display usage instructions
usage() {
    echo "Usage: $0 [option]"
    echo "Options:"
    echo "  all          Run all tests"
    echo "  mutation     Run only mutation tests"
    echo "  parsing      Run only parsing tests"
    exit 1
}

# Check if an argument is provided
if [ $# -eq 0 ]; then
    usage
fi

# Handle the provided option
case $1 in
    all)
        echo "Running all tests..."
        python -m unittest discover -s test -p "test_*.py" -v
        ;;
    mutation)
        echo "Running mutation tests..."
        python -m unittest discover -s test -p "test_mutation*.py" -v
        ;;
    parsing)
        echo "Running parsing tests..."
        python -m unittest discover -s test -p "test_parsing*.py" -v
        ;;
    *)
        echo "Invalid option: $1"
        usage
        ;;
esac