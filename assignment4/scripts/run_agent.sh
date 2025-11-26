#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

export PYTHONPATH=.

python scripts/run_agent.py \
    --input data/aime24.jsonl \
    --output_dir results \
    --mode tool \
    --max_agent_steps 20 \
    --temperature 0.6 \
    --max_tokens 8192 \
    --num_rollouts 4 