#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

export PYTHONPATH=.

python scripts/run_agent.py \
    --input data/nq_test_100.jsonl \
    --output_dir results \
    --mode search \
    --num_search_results 5 \
    --max_agent_steps 5 \
    --temperature 0.0 \
    --max_tokens 2048 

