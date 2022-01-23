#!/usr/bin/env bash

TEMPORAL_FOLDER=${1:-landing/temporal}

mkdir -p "$TEMPORAL_FOLDER"

cat links | xargs -n1 wget -P "$TEMPORAL_FOLDER"
