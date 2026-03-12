#!/usr/bin/env bash
set -e
docker build -t ltltutor .
docker run --rm -it -p 5000:5000 -e SECRET_KEY="$(openssl rand -hex 32)" ltltutor
