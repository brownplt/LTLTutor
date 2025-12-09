#!/bin/bash

# Build and run LTLTutor Docker container
# This script builds the Docker image and runs it with the necessary configuration

set -e  # Exit on error

echo "Building LTLTutor Docker image..."
docker build . -t ltltutor

echo "Running LTLTutor container..."
docker run --rm -it -p 5000:5000 -e SECRET_KEY=secret ltltutor
