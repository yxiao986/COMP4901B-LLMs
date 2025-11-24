#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# Set Python path to current directory so python can find 'src' module
export PYTHONPATH=.

# --- Task 2.1: Run Baseline (No Search) ---
echo "Running Task 2.1: Baseline (No Search)..."
python scripts/run_agent.py \
    --input data/nq_test_100.jsonl \
    --output_dir results \
    --mode nosearch \
    --temperature 0.0 \
    --max_tokens 2048

# --- Task 2.2: Run Agent (With Search) ---
echo "Running Task 2.2: Agent (With Search)..."
python scripts/run_agent.py \
    --input data/nq_test_100.jsonl \
    --output_dir results \
    --mode search \
    --num_search_results 5 \
    --max_agent_steps 5 \
    --temperature 0.0 \
    --max_tokens 2048

echo "All tasks completed!"