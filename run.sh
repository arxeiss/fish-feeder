#!/bin/bash
if test -f ".env"; then
    set -a
    source .env
    set +a
fi

python3 feed.py
