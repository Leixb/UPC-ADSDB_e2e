#!/usr/bin/env bash

set -e

TEMPORAL_FOLDER=${1:-landing/temporal}

mkdir -p "$TEMPORAL_FOLDER"

./download.sh "$TEMPORAL_FOLDER"

echo START LANDING
python landing.py "$TEMPORAL_FOLDER"

echo START FORMATTED
python formatted.py

echo START FORMATTED
python trusted.py

echo START EXPLOITATION
python exploitation.py

echo START MODELLING
python modelling.py

echo DONE
