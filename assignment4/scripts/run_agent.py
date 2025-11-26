import argparse
import datetime
import logging
import os
import json
import shutil
from tqdm import tqdm
from dotenv import load_dotenv
from openai import OpenAI
from src.agent import Agent 

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description="Run agent with or without searh")

    parser.add_argument(
        "--input",
        type=str,
        default="data/nq_test_100.jsonl",
        help="Path to the input dataset (JSONL)"
    )

    parser.add_argument(
        "--output_dir", 
        type=str, 
        default="results", 
        help="Directory to save results"
    )

    parser.add_argument(
        "--mode",
        type=str,
        choices=["tool","notool"],
        help="Running mode: 'tool' (Agent) or 'notool' (Baseline)"
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit the number of examples to run (for debugging)"
    )

    parser.add_argument(
        "--max_agent_steps", 
        type=int, 
        default=20,
        help="Maximum steps for the agent loop (Default: 20)"
    )

    parser.add_argument(
        "--temperature", 
        type=float, 
        default=0.6,
        help="LLM sampling temperature (Default: 0.0)"
    )

    parser.add_argument(
        "--max_tokens", 
        type=int, 
        default=8192,
        help="Max generation tokens (Default: 8192)"
    )

    parser.add_argument(
        "--num_rollouts", 
        type=int, 
        default=4,
        help="Number of rollouts per problem (Default: 4)"
    )

    return parser.parse_args()

def load_data(file_path):
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data

def run_baseline(client, model_name, problem, temperature, max_tokens):
    system_message = """
        You are solving AIME (American Invitational Mathematics Examination) problems. Put your final answer in \\boxed{} format.
        """

    messages = [
        {"role":"system","content":system_message},
        {"role":"user", "content": problem}
    ]

    try:
        response_stream = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True, 
            timeout=600.0
        )

        collected_content = []
        
        for chunk in response_stream:

            if chunk.choices:
                chunk_content = chunk.choices[0].delta.content
                if chunk_content:
                    collected_content.append(chunk_content)

        full_answer = "".join(collected_content)
        return full_answer

    except Exception as e:
        logger.error(f"Baseline generation failed: {e}")
        return "Error generating response"

def main():

    # 1. Load environment variables. Parse arguments
    load_dotenv()
    deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")

    if not deepseek_api_key:
        logger.warning("DEEPSEEK_API_KEY not found in environment variables.")

    args = parse_args()

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(args.output_dir, exist_ok=True)

    pred_path_timestamp = os.path.join(args.output_dir, f"predictions_{args.mode}_{timestamp}.jsonl")
    pred_path_latest = os.path.join(args.output_dir, f"predictions_{args.mode}.jsonl")

    # 2. Initialize agent or client

    if args.mode == "tool":
        num_rollouts = args.num_rollouts
        agent = None
    else:
        num_rollouts = 1
        client=OpenAI(
            api_key=deepseek_api_key,
            base_url="https://api.deepseek.com/v1",
            timeout=600
        )
        logger.info(f"Client initialized in NO-TOOL mode (Temp={args.temperature}).")

    # 3. Load data
    if not os.path.exists(args.input):
        raise FileNotFoundError(f"Input file not found: {args.input}")

    dataset = load_data(args.input)
    if args.limit:
        dataset = dataset[:args.limit]
        logger.info(f"Limiting execution to first {args.limit} examples.")

    # 4. Main loop
    predictions = []
    logger.info(f"Starting inference on {len(dataset)} examples...")

    for item in tqdm(dataset):
        problem = item.get('problem')
        ground_truths = item.get('answer')
        item_id = item.get('id','unknown')

        for i in range(num_rollouts):
            final_answer = ""

            try:
                if args.mode == "tool":
                    # Run agent
                    agent = Agent(
                        deepseek_api_key=deepseek_api_key,
                        model_name="deepseek-chat",
                        max_agent_steps=args.max_agent_steps,
                        max_tokens=args.max_tokens
                    )
                    logger.info(f"Agent initialized in TOOL mode (Temp={args.temperature}).")
                    final_answer = agent.run(problem)

                else:
                    final_answer = run_baseline(client, "deepseek-chat", problem, args.temperature, args.max_tokens)

                # Append predictions
                predictions.append({
                    "id":item_id,
                    "rollout_id":i,
                    "problem":problem,
                    "answer": ground_truths,
                    "llm_response": final_answer
                })

            except Exception as e:
                logger.error(f"Error processing problem id {item_id}: {e}")

                # Append error to predictions
                predictions.append({
                    "id":item_id,
                    "problem":problem,
                    "answer": ground_truths,
                    "llm_response": "\\boxed{error}"
                })
    
    # 5. Write in outputs
    with open(pred_path_timestamp, 'w', encoding='utf-8') as f:
        for p in predictions:
            f.write(json.dumps(p) + '\n')
    logger.info(f"Saved archival predictions: {pred_path_timestamp}")

    shutil.copy(pred_path_timestamp, pred_path_latest)
    logger.info(f"Updated latest predictions:   {pred_path_latest}")


if __name__=="__main__":
    main()
    