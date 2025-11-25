#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

if [ -z "$DEEPSEEK_API_KEY" ]; then
    echo "Error: DEEPSEEK_API_KEY is not set. Please check your .env file or environment variables."
    exit 1
fi

export PYTHONPATH=.

# --- Grade with EM ---
python scripts/grade_with_em.py \
    --input results/predictions_nosearch.jsonl \
    --output results/grading_baseline_results_em.json

# --- Grade with llm ---
python scripts/grade_with_llm_judge.py \
    --input results/predictions_nosearch.jsonl \
    --model deepseek-chat \
    --base_url https://api.deepseek.com/v1 \
    --api_key "$DEEPSEEK_API_KEY" \
    --output results/grading_baseline_results_llm_judge.json

echo "All evaluation finished!"