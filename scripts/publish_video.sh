#!/bin/bash

# Script to generate and publish a video via Post Bridge.

if [ -x "$(command -v python3)" ]; then
  PYTHON=python3
else
  PYTHON=python
fi

"$PYTHON" src/cron.py publish
