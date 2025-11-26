import json
from openai import OpenAI
from src.execute_python_code import execute_python_code

class Agent:
    def __init__(
        self,
        deepseek_api_key: str,
        model_name: str = "deepseek-chat",
        base_url: str = "https://api.deepseek.com/v1",
        max_agent_steps: int = 20,
        temperature: float = 0.6,
        max_tokens: int = 8192
    ):
        # LLM Configuration
        self.llm_client = OpenAI(
            api_key=deepseek_api_key,
            base_url=base_url,
            timeout=600
        )
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Agent Loop Control
        self.current_step = 0
        self.max_agent_steps = max_agent_steps

        # State Tracking
        self.conversation_history = []
        self.question = None
        self.final_answer = None
        
        # Tool Configuration
        self.tools = [{
            "type": "function",
            "function": {
                "name": "execute_python_code",
                "description": "Execute Python code to perform calculations and verify solutions",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "Python code to execute"
                        }
                    },
                    "required": ["code"]
                }
            }
        }]
        self.available_tools_map = self._build_tool_executors()


    def _build_tool_executors(self) -> dict:
        """
        Build the mapping from tools name to executors.
        """
        return {
            "execute_python_code": self._execute_python_tool
        }

    def _execute_python_tool(self, code: str) -> str:
        """
        Internal executor for the 'execute_python_code' tool.
        """
        print(f"--- Agent is executing python code ---")
        try:
            stdout, stderr, return_val = execute_python_code(code)
            
            output_parts = []
            if stdout:
                output_parts.append(f"Standard Output:\n{stdout}")
            if stderr:
                output_parts.append(f"Standard Error:\n{stderr}")
            if return_val:
                output_parts.append(f"Return Value:\n{return_val}")
            
            if not output_parts:
                result_str = "Code executed successfully with no output."
            else:
                result_str = "\n".join(output_parts)
            
            return result_str

        except Exception as e:
            error_msg = f"Tool Execution Internal Error: {str(e)}"
            return error_msg


    def run(self, question:  str) -> (str, list):
        """
        Execute agent loop.

        Returns: final_answer
        """
        self.question = question

        # Construct system message
        system_message = """You are solving AIME (American Invitational Mathematics Examination) problems.

        Reason step by step. 

        You have access to Python code execution via the execute_python_code tool. Use it to perform calculations, verify solutions, or explore patterns.

        Put your final answer in \\boxed{} format.

        Available Python modules: math, fractions, itertools, sympy, numpy"""
        
        # Construct conversation
        self.conversation_history = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": question}
        ]
        
        # Execute agent loop
        for step in range(self.max_agent_steps):
            self.current_step = step
            print(f"--- Agent step {step+1} ---")

            # 1. LLM thinking
            response = self.llm_client.chat.completions.create(
                model=self.model_name,
                messages=self.conversation_history,
                tools=self.tools,
                tool_choice="auto",
                temperature=self.temperature,
                max_tokens=self.max_tokens, 
                timeout=600.0
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
                        tool_output_string = function_to_call(**function_args)
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
                return final_answer

        # 4. Maximum step reached
        print(f"--- Maximum agent step reached ---")

        # Fall back to baseline model
        force_answer_message = {
            "role": "user",
            "content": "You have reached the maximum number of search steps. Please synthesize the information you have gathered so far, or use your internal knowledge to provide the best possible answer to the original question. You MUST put your final answer in \\boxed{} format."
        }
        self.conversation_history.append(force_answer_message)

        try:
            response = self.llm_client.chat.completions.create(
                model=self.model_name,
                messages=self.conversation_history,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            final_answer = response.choices[0].message.content

        except Exception as e:
            print(f"Error in final fallback: {e}")
            final_answer = "\\boxed{error}"

        return final_answer

    