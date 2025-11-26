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
from src.metrics import extract_answer_from_text

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
        choices=["search","nosearch"],
        help="Running mode: 'search' (Agent) or 'nosearch' (Baseline)"
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit the number of examples to run (for debugging)"
    )

    parser.add_argument(
        "--num_search_results", 
        type=int, 
        default=3,
        help="Number of search results to retrieve per step (Default: 3)"
    )

    parser.add_argument(
        "--max_agent_steps", 
        type=int, 
        default=5,
        help="Maximum steps for the agent loop (Default: 5)"
    )

    parser.add_argument(
        "--temperature", 
        type=float, 
        default=0.0,
        help="LLM sampling temperature (Default: 0.0)"
    )

    parser.add_argument(
        "--max_tokens", 
        type=int, 
        default=2048,
        help="Max generation tokens (Default: 2048)"
    )

    return parser.parse_args()

def load_data(file_path):
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data

def run_baseline(client, model_name, question, temperature, max_tokens):
    system_message = f"""
        You are a helpful assistant. 
        Please answer the user's question directly and concisely. 
        You MUST provide your final answer wrapped in <answer> and </answer> tags.

        CRITICAL OUTPUT RULES:
        1.  Thinking Process: You may think freely before answering.
        2.  Final Answer: You MUST terminate your response with the exact answer wrapped in XML tags: <answer>...</answer>.
        3.  NO CHATTER: Do not say "I hope this helps" or "The answer is". Just give the tagged answer at the end.
        4.  CONCISENESS: The content inside <answer> tags must be EXTREMELY short (1-5 words).
        5.  NO LISTS: If the answer involves multiple items, provide only the main one or a summary count (e.g., "5 types"). DO NOT list them all.
        
        Format Example:
        User: Who is the CEO of Google?
        Assistant: Sundar Pichai became CEO in 2015... <answer>Sundar Pichai</answer>
        """

    few_shot_examples = [
            {
                "role": "user", 
                "content": "When was the last time anyone was on the moon?"
            },
            {
                "role": "assistant", 
                "content": "The last manned mission to the Moon was Apollo 17. The mission took place in December 1972. Therefore, the last time anyone was on the moon was December 1972.\n<answer>December 1972</answer>"
            },
            {
                "role": "user",
                "content": "how many rings does ariana grande have?" 
            },
            {
                "role": "assistant",
                "content": "Ariana Grande has 7 rings according to her song. <answer>seven</answer>" 
            }
        ]

    messages = [
        {"role":"system","content":system_message},
        *few_shot_examples,
        {"role":"user", "content": question}
    ]

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

        clean_answer = extract_answer_from_text(response.choices[0].message.content)
        return clean_answer
    except Exception as e:
        logger.error(f"Baseline generation failed: {e}")
        return "Error generating response"

def main():

    # 1. Load environment variables. Parse arguments
    load_dotenv()
    deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
    serper_api_key = os.getenv("SERPER_API_KEY")

    if not deepseek_api_key:
        logger.warning("DEEPSEEK_API_KEY not found in environment variables.")
    elif not serper_api_key:
        logger.warning("SERPER_API_KEY not found in environment variables.")

    args = parse_args()

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(args.output_dir, exist_ok=True)

    pred_path_timestamp = os.path.join(args.output_dir, f"predictions_{args.mode}_{timestamp}.jsonl")
    pred_path_latest = os.path.join(args.output_dir, f"predictions_{args.mode}.jsonl")

    traj_path_timestamp = os.path.join(args.output_dir, f"agent_trajectories_{timestamp}.jsonl")
    traj_path_latest = os.path.join(args.output_dir, "agent_trajectories.jsonl")

    # 2. Initialize agent or client
    agent = None
    client = None

    if args.mode == "search":
        if not serper_api_key:
            raise ValueError("SERPER_API_KEY is required for search mode.")

        agent = Agent(
            deepseek_api_key=deepseek_api_key,
            serper_api_key=serper_api_key,
            model_name="deepseek-chat",
            max_agent_steps=args.max_agent_steps,
            num_search_results=args.num_search_results,
            max_tokens=args.max_tokens
        )
        logger.info(f"Agent initialized in SEARCH mode (Temp={args.temperature}).")

    else:
        client=OpenAI(
            api_key=deepseek_api_key,
            base_url="https://api.deepseek.com/v1"
        )
        logger.info(f"Client initialized in NO-SEARCH mode (Temp={args.temperature}).")

    # 3. Load data
    if not os.path.exists(args.input):
        raise FileNotFoundError(f"Input file not found: {args.input}")

    dataset = load_data(args.input)
    if args.limit:
        dataset = dataset[:args.limit]
        logger.info(f"Limiting execution to first {args.limit} examples.")

    # 4. Main loop
    predictions = []
    trajectories = []

    logger.info(f"Starting inference on {len(dataset)} examples...")

    for item in tqdm(dataset):
        question = item.get('question')
        ground_truths = item.get('answers',[])
        item_id = item.get('id','unknown')

        final_answer = ""
        final_answer_raw = ""

        try:
            if args.mode == "search":
                # Run agent
                final_answer_raw, steps = agent.run(question)
            
                # Append trajectories
                trajectories.append({
                    "id":item_id,
                    "question":question,
                    "ground_truths":ground_truths,
                    "trajectory":{
                        "question":question,
                        "steps":steps,
                        "final_answer":final_answer_raw,
                        "total_search_steps": len([s for s in steps if s['action']=='search'])
                    }
                })

                # Extract the answer
                final_answer = extract_answer_from_text(final_answer_raw)

            else:
                final_answer_raw = run_baseline(client, "deepseek-chat", question, args.temperature, args.max_tokens)
                final_answer = extract_answer_from_text(final_answer_raw)

            # Append predictions
            predictions.append({
                "id":item_id,
                "question":question,
                "answers": ground_truths,
                "llm_response": final_answer
            })

        except Exception as e:
            logger.error(f"Error processing question id {item_id}: {e}")

            # Append error to predictions
            predictions.append({
                "id":item_id,
                "question":question,
                "answers": ground_truths,
                "llm_response": "<error>"
            })
    
    # 5. Write in outputs
    with open(pred_path_timestamp, 'w', encoding='utf-8') as f:
        for p in predictions:
            f.write(json.dumps(p) + '\n')
    logger.info(f"Saved archival predictions: {pred_path_timestamp}")

    shutil.copy(pred_path_timestamp, pred_path_latest)
    logger.info(f"Updated latest predictions:   {pred_path_latest}")

    if args.mode == "search" and traj_path_timestamp:
        with open(traj_path_timestamp, 'w', encoding='utf-8') as f:
            for t in trajectories:
                f.write(json.dumps(t) + '\n')
        logger.info(f"Saved archival trajectories: {traj_path_timestamp}")
        
        shutil.copy(traj_path_timestamp, traj_path_latest)
        logger.info(f"Updated latest trajectories:   {traj_path_latest}")


if __name__=="__main__":
    main()
    