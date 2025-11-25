import json
from openai import OpenAI
from src.tools import get_tools_list
from src.search import search, format_search_results
from src.browser import browse

class Agent:
    def __init__(
        self,
        deepseek_api_key: str,
        serper_api_key: str,
        model_name: str = "deepseek-chat",
        base_url: str = "https://api.deepseek.com/v1",
        max_agent_steps: int = 5,
        num_search_results: int = 3,
        temperature: float = 0.0,
        max_tokens: int = 2048
    ):
        # LLM Configuration
        self.llm_client = OpenAI(
            api_key=deepseek_api_key,
            base_url=base_url
        )
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Agent Loop Control
        self.current_step = 0
        self.max_agent_steps = max_agent_steps

        # State Tracking
        self.conversation_history = []
        self.trajectory_steps = []
        self.question = None
        self.final_answer = None
        
        # Tool Configuration
        self.tools = get_tools_list()
        self.available_tools_map = self._build_tool_executors()

        # Search Configuration
        self.serper_api_key = serper_api_key
        self.num_search_results = num_search_results

        # Other Configuration

    def _build_tool_executors(self) -> dict:
        """
        Build the mapping from tools name to executors.
        """
        return {
            "search": self._execute_search,
            "browse": self._execute_browse
        }

    def _execute_search(self, step_number: int, query: str) -> str:
        """
        Internal executor for the 'search' tool.
        """
        print(f"--- Agent is searching: {query} ---")
        try:
            # Call search API
            raw_results = search(
                query=query,
                api_key=self.serper_api_key,
                num_results=self.num_search_results
            )

            # log trajectory steps
            log_entry = {
                "step_number": step_number,
                "action": "search",
                "query": query,
                "num_docs_requested": self.num_search_results,
                "retrieved_documents": raw_results  
            }
            self.trajectory_steps.append(log_entry)
            
            return format_search_results(raw_results)

        except Exception as e:
            print(f"--- Searching Error: {e}---")
            log_entry = {
                "step_number": step_number,
                "action": "search",
                "query": query,
                "error": str(e)
            }
            self.trajectory_steps.append(log_entry)

            error_msg = f"Searching Error: {e} "
            return error_msg

    def _execute_browse(self, step_number:int, url:str) -> str:
        """
        Internal executor for the 'browse' tool.
        """
        print(f"--- Agent is browsing: {url} ---")
        try:
            # Execute browsing
            page_content = browse(url)

            # Log trajectory (truncate the content)
            log_entry = {
                "step_number": step_number,
                "action": "browse",
                "url": url,
                "content_preview": page_content[:500] + "..." 
            }
            self.trajectory_steps.append(log_entry)

            return page_content
        
        except Exception as e:
            error_msg = f"Browsing failed: {str(e)}"
            self.trajectory_steps.append({
                "step_number": step_number,
                "action": "browse",
                "url": url,
                "error": error_msg
            })
            return error_msg


    def run(self, question:  str) -> (str, list):
        """
        Execute agent loop.

        Returns: (final_answer, trajectory_steps)
        """
        self.question = question

        # Construct system message
        system_message = f"""You are a helpful and capable question-answering assistant. Your task is to answer user questions accurately using the provided tools.

        Your Goal: Answer the user's question using the provided tools.

        Available Tools:
        - search: Use this tool to search the internet for facts, current events, public figures, and other information.
        - browse: Use this tool to read the FULL text of a specific URL.

        Your Workflow:
        1. ANALYZE: Determine if you need external information to answer the question.
        2. SEARCH: If needed, use the 'search' tool to gather information. You can search multiple times if the first result is not sufficient.
        3. BROWSE: If a search snippet is cut off, ambiguous, or lacks detail, use BROWSE on that URL to get the facts.
        4. SYNTHESIZE: Once you have enough information, formulate your answer.
        5. FINAL ANSWER: You MUST provide your final answer wrapped in <answer> and </answer> tags.

        CRITICAL OUTPUT RULES:
        1.  Thinking Process: You may think freely before answering.
        2.  Final Answer: You MUST terminate your response with the exact answer wrapped in XML tags: <answer>...</answer>.
        3.  NO CHATTER: Do not say "I hope this helps" or "The answer is" "Yes,". Just give the tagged answer at the end.
        4.  CONCISENESS: The content inside <answer> tags must be EXTREMELY short (1-5 words).
        5.  NO LISTS: If the answer involves multiple items, provide only the main one or a summary count (e.g., "5 types"). DO NOT list them all.

        Format Example:
        User: Who is the CEO of Google?
        Assistant: Sundar Pichai became CEO in 2015... <answer>Sundar Pichai</answer>
        """
        # Construct few-shot example
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

        # Construct conversation
        self.conversation_history = [
            {"role": "system", "content": system_message},
            *few_shot_examples,
            {"role": "user", "content": question}
        ]

        # Construct trajectory
        self.trajectory_steps = []
        
        # Execute agent loop
        for step in range(self.max_agent_steps):
            self.current_step = step
            current_step_number = step+1
            print(f"--- Agent step {step+1} ---")

            # 1. LLM thinking
            response = self.llm_client.chat.completions.create(
                model=self.model_name,
                messages=self.conversation_history,
                tools=self.tools,
                tool_choice="auto",
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )

            response_message = response.choices[0].message

            # Update conversation
            self.conversation_history.append(response_message)

            # 2. Check if tool calls, execute one at a time
            if response_message.tool_calls:
                tool_call = response_message.tool_calls[0]
                function_name = tool_call.function.name

                # 3. Check if tool available
                if function_name in self.available_tools_map:
                    function_to_call = self.available_tools_map[function_name]

                    try:
                        # Execute tool
                        function_args = json.loads(tool_call.function.arguments)
                        tool_output_string = function_to_call(
                            step_number=current_step_number, 
                            **function_args
                        )
                        # Update conversation
                        self.conversation_history.append(
                            {
                                "tool_call_id": tool_call.id,
                                "role": "tool",
                                "name": function_name,
                                "content": tool_output_string,
                            }
                        )

                    except Exception as e:
                        print(f"--- Error: {e} happened when executing tools")
                
                else:
                    # Unknown tools are called
                    print(f"--- Agent error: LLM tried to call unknown tool'{function_name}'")

            else:
                # No tool call
                print("--- Agent decides to give final answer ---")
                final_answer = response_message.content
                self.trajectory_steps.append({
                    "step_number": current_step_number,
                    "action": "final_answer",
                    "answer_raw": final_answer
                })

                return final_answer, self.trajectory_steps

        # 4. Maximum step reached
        print(f"--- Maximum agent step reached ---")

        # Fall back to baseline model
        force_answer_message = {
            "role": "user",
            "content": "You have reached the maximum number of search steps. Please synthesize the information you have gathered so far, or use your internal knowledge to provide the best possible answer to the original question. You MUST wrap the answer in <answer> tags."
        }
        self.conversation_history.append(force_answer_message)

        try:
            response = self.llm_client.chat.completions.create(
                model=self.model_name,
                messages=self.conversation_history,
                temperature=0.0,
                max_tokens=self.max_tokens
            )
            final_answer = response.choices[0].message.content

        except Exception as e:
            print(f"Error in final fallback: {e}")
            final_answer = "<answer>Error generating final answer</answer>"

        # Append trajectory steps
        self.trajectory_steps.append({
            "step_number": self.max_agent_steps,
            "action": "force_answer",
            "answer_raw": final_answer
        })

        return final_answer, self.trajectory_steps

    