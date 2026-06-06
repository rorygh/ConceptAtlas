#!/usr/bin/env bash
# Load RUNPOD_* vars from ~/.bashrc, bypassing the interactive-shell guard.
while IFS= read -r line; do
  [[ "$line" =~ ^export\ RUNPOD_ ]] && export "${line#export }"
done < ~/.bashrc
exec uvicorn api.main:app --port 8000 "$@"
