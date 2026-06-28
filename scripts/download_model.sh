#!/usr/bin/env bash
set -euo pipefail

MODEL="vosk-model-en-us-0.22"
URL="https://alphacephei.com/vosk/models/${MODEL}.zip"
DATA_DIR="$(dirname "$0")/../data"

echo "Downloading ${MODEL}..."
wget -q --show-progress "$URL" -O "/tmp/${MODEL}.zip"

echo "Extracting to ${DATA_DIR}/"
unzip -q "/tmp/${MODEL}.zip" -d "$DATA_DIR"

echo "Cleaning up..."
rm "/tmp/${MODEL}.zip"

echo "Done. Model at ${DATA_DIR}/${MODEL}/"
