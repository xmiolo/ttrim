#!/usr/bin/env bash
# UserPromptSubmit hook — detects --no-compress and --metrics in the prompt
# and writes flag files that compress_md.py reads during the same turn.

_FLAG_BYPASS="/tmp/.ttrim_no_compress"
_FLAG_METRICS="/tmp/.ttrim_metrics"

input=$(cat)

# Parse prompt field from JSON (jq preferred, Python as fallback)
if command -v jq &>/dev/null; then
    prompt=$(echo "$input" | jq -r '.prompt // ""')
else
    prompt=$(echo "$input" | python3 -c "import json,sys; print(json.load(sys.stdin).get('prompt',''))" 2>/dev/null || echo "")
fi

# --no-compress bypass
if echo "$prompt" | grep -qE '(--no-compress|--bypass-compress)'; then
    touch "$_FLAG_BYPASS"
else
    rm -f "$_FLAG_BYPASS"
fi

# --metrics stats
if echo "$prompt" | grep -qE '\-\-metrics'; then
    touch "$_FLAG_METRICS"
else
    rm -f "$_FLAG_METRICS"
fi
