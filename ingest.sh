#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "==> Fetching MIT catalog..."
python -m ingest.fetch_mit

echo "==> Parsing courses..."
python -m ingest.parse_courses

echo "==> Embedding and building similarity matrix (this takes ~60s on CPU)..."
python -m ingest.embed_courses

echo "==> Ingestion complete."
