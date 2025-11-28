import argparse
import logging
import os
import json
from tqdm import tqdm
from dotenv import load_dotenv
from src.real_agent import RealAgent 

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description="Run agent with or without searh")

    parser.add_argument(
        "--input",
        type=str,
        default= "data/tasks.jsonl",
        help="task list in the format [{'id':..., 'question':...}]"
    )

    parser.add_argument(
        "--output_dir", 
        type=str, 
        default="results", 
        help="Directory to save results"
    )

    parser.add_argument(
        "--num_search_results", 
        type=int, 
        default=5,
        help="Number of search results to retrieve per step (Default: 5)"
    )

    parser.add_argument(
        "--max_agent_steps", 
        type=int, 
        default=10,
        help="Maximum steps for the agent loop (Default: 10)"
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
        default=8192,
        help="Max generation tokens (Default: 8192)"
    )

    return parser.parse_args()


def main():

    # 1. Load environment variables. Parse arguments
    load_dotenv()
    deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
    serper_api_key = os.getenv("SERPER_API_KEY")
    github_token = os.getenv("GITHUB_TOKEN")
    notion_token = os.getenv("NOTION_API_KEY")
    notion_page_id = os.getenv("NOTION_PAGE_ID")    

    if not deepseek_api_key:
        logger.warning("DEEPSEEK_API_KEY not found in environment variables.")
    elif not serper_api_key:
        logger.warning("SERPER_API_KEY not found in environment variables.")
    elif not github_token:
        logger.warning("GITHUB_TOKEN not found in environment variables.") 

    args = parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    traj_path = os.path.join(args.output_dir, "real_agent_trajectories.jsonl")
    thought_processes_path = os.path.join(args.output_dir, "real_agent_thought_processes.jsonl")

    # 2. Initialize agent
    agent = RealAgent(
        deepseek_api_key=deepseek_api_key,
        serper_api_key=serper_api_key,
        github_token=github_token,
        notion_token=notion_token,
        notion_page_id=notion_page_id,
        model_name="deepseek-chat",
        max_agent_steps=args.max_agent_steps,
        num_search_results=args.num_search_results,
        max_tokens=args.max_tokens
    )

    # 3. Load tasks
    with open(args.input, 'r', encoding='utf-8') as f:
        raw_tasks = f.read()

    stripped = raw_tasks.lstrip()
    if not stripped:
        tasks = []
    elif stripped.startswith("["):
        tasks = json.loads(stripped)
    else:
        tasks = [
            json.loads(line)
            for line in raw_tasks.splitlines()
            if line.strip()
        ]
    logger.info(f"Loaded {len(tasks)} tasks from {args.input}.")

    # 4. Main loop
    thought_processes = []
    trajectories = []

    for item in tqdm(tasks, desc="Processing questions"):
        question = item.get('question')
        item_id = item.get('id','unknown')

        final_answer = ""

        try:
            # Run agent
            final_answer, full_thought_process, steps = agent.run(question)
            
            # Append trajectories
            trajectories.append({
                "id":item_id,
                "question":question,
                "trajectory":{
                    "question":question,
                    "steps":steps,
                    "final_answer":final_answer,
                    "total_search_steps": len([s for s in steps if s['action']=='search'])
                }
            })


            # Append thought_processes
            thought_processes.append({
                "id":item_id,
                "question":question,
                "llm_response": full_thought_process
            })

        except Exception as e:
            logger.error(f"Error processing question id {item_id}: {e}")

            # Append error to predictions
            thought_processes.append({
                "id":item_id,
                "question":question,
                "llm_response": "Error during processing. "
            })
    
    # 5. Write in outputs
    with open(traj_path, 'w', encoding='utf-8') as f:
        for t in trajectories:
            f.write(json.dumps(t) + '\n')
    logger.info(f"Saved archival trajectories: {traj_path}")

    with open(thought_processes_path, 'w', encoding='utf-8') as f:
        for tp in thought_processes:
            f.write(json.dumps(tp) + '\n')
    logger.info(f"Saved thought processes: {thought_processes_path}")
        
if __name__=="__main__":
    main()
    