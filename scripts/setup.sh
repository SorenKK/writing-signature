#!/usr/bin/env bash
# Create the Python environment for writing-signature and download spaCy models.
# Usage: bash scripts/setup.sh [lang ...]     (default: en it)
set -euo pipefail
cd "$(dirname "$0")/.."

for tool in pandoc pdftotext; do
  command -v "$tool" >/dev/null || echo "WARNING: $tool not found (needed by extract_text.py)"
done

if command -v uv >/dev/null; then
  uv venv -q .venv && uv pip install -q -p .venv/bin/python -r requirements.txt
else
  python3 -m venv .venv && .venv/bin/pip install -q -r requirements.txt
fi

declare -A MODEL=([en]=en_core_web_md [it]=it_core_news_lg)
for lang in "${@:-en it}"; do
  for l in $lang; do
    m="${MODEL[$l]:-}"
    [ -n "$m" ] || { echo "No model configured for '$l': add it to LANGUAGES in scripts/stylometry.py"; continue; }
    .venv/bin/python -m spacy download "$m" | tail -1
  done
done
echo "Ready. PY=$(pwd)/.venv/bin/python"
