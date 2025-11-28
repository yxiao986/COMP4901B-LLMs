import json
from openai import OpenAI
from src.tools.tool_list import get_tools_list
from src.tools.web_tools import search, format_search_results, browse
from src.tools.report_tools import generate_html_report, create_notion_page, append_to_notion_page
from src.tools.github_tools import create_github_branch, create_or_update_file, list_github_directory, read_github_file, create_github_issue
from src.tools.slack_tool import send_slack_message


class RealAgent:
    def __init__(
        self,
        deepseek_api_key: str,
        serper_api_key: str,
        github_token: str,
        notion_token: str,
        notion_page_id: str,
        model_name: str = "deepseek-chat",
        base_url: str = "https://api.deepseek.com/v1",
        slack_webhook_url: str = "",
        max_agent_steps: int = 10,
        num_search_results: int = 5,
        temperature: float = 0.0,
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
        self.trajectory_steps = []
        self.question = None
        self.final_answer = None
        self.full_thought_process = ""
        
        # Tool Configuration
        self.tools = get_tools_list()
        self.available_tools_map = self._build_tool_executors()

        # Search Configuration
        self.serper_api_key = serper_api_key
        self.num_search_results = num_search_results

        # Github Configuration
        self.github_token = github_token

        # Notion Configuration
        self.notion_token = notion_token
        self.notion_page_id = notion_page_id

        # Slack Configuration
        self.webhook_url = slack_webhook_url

    def _build_tool_executors(self) -> dict:
        """
        Build the mapping from tools name to executors.
        """
        return {
            "search": self._execute_search,
            "browse": self._execute_browse,
            "list_github_directory": self._execute_list_github,
            "read_github_file": self._execute_read_github,
            "create_github_branch": self._execute_create_branch,
            "create_or_update_file": self._execute_write_file,
            "generate_html_report": self._execute_generate_report,
            "create_notion_page": self._execute_create_notion_page,
            "append_to_notion_page": self._execute_append_notion_page,
            "create_github_issue": self._execute_create_github_issue,   
            "send_slack_message": self._execute_send_slack_message
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
            return self._handle_tool_error(step_number, "search", str(e))

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
            return self._handle_tool_error(step_number, "browse", str(e))
        
    def _execute_list_github(self, repo_name, path, branch="main", step_number=0):
        try:
            print(f"--- Agent is Listing {path} in {branch} branch ---")
            result = list_github_directory(repo_name, path, self.github_token, branch)
            self.trajectory_steps.append({
                "step": step_number, "action": "list_files", "output": result
            })
            return result
        except Exception as e:
            return self._handle_tool_error(step_number, "list_github_directory", str(e))

    def _execute_read_github(self, repo_name, file_path, branch="main", step_number=0):
        try:
            print(f"--- Agent is Reading {file_path} in {branch} branch ---")
            result = read_github_file(repo_name, file_path, self.github_token,branch)
            # Log truncated content to keep logs clean
            log_content = result[:500] + "..." if len(result) > 500 else result
            self.trajectory_steps.append({
                "step": step_number, "action": "read_file", "output": log_content
            })
            return result
        except Exception as e:
            return self._handle_tool_error(step_number, "read_github_file", str(e))

    def _execute_create_branch(self, repo_name, new_branch_name, base_branch, step_number=0):
        try:
            print(f"--- Agent is Creating Branch {new_branch_name} ---")
            result = create_github_branch(repo_name, new_branch_name, base_branch, self.github_token)
            self.trajectory_steps.append({
                "step": step_number, "action": "create_branch", "output": result
            })
            return result
        except Exception as e:
            return self._handle_tool_error(step_number, "create_github_branch", str(e))

    def _execute_write_file(self, repo_name, file_path, file_content, commit_message, branch_name, step_number=0):
        try:
            print(f"--- Agent is Writing File {file_path} to {branch_name} ---")
            result = create_or_update_file(repo_name, file_path, file_content, commit_message, branch_name, self.github_token)
            self.trajectory_steps.append({
                "step": step_number, "action": "write_file", "output": result
            })
            return result
        except Exception as e:  
            return self._handle_tool_error(step_number, "create_or_update_file", str(e))
        
    def _execute_generate_report(self, filename, title, pages, step_number=0):
        try:
            print(f"--- Agent is Generating Interactive Report: {filename} ---")
            result = generate_html_report(filename, title, pages)
            page_titles = [p['title'] for p in pages]
            self.trajectory_steps.append({
                "step": step_number,
                "action": "tool_call",
                "tool": "generate_html_report",
                "args": {"filename": filename, "page_count": len(pages)},
                "output": f"Generated site with pages: {page_titles}"
            })
            return result
        except Exception as e:
            return self._handle_tool_error(step_number, "generate_html_report", str(e))
        
    def _execute_create_notion_page(self, title, content, step_number=0):
        try:
            print(f"--- Agent is Creating Notion Page: {title} ---")
            result = create_notion_page(title, content, self.notion_token, self.notion_page_id)
            self.trajectory_steps.append({
                "step": step_number,
                "action": "tool_call",
                "tool": "create_notion_page",
                "args": {"title": title},
                "output": f"Created Notion page with ID: {result}"
            })
            return result
        except Exception as e:
            return self._handle_tool_error(step_number, "create_notion_page", str(e))
        
    def _execute_append_notion_page(self, target_page_id, content, step_number=0):  
        try:
            print(f"--- Agent is Appending to Notion Page ID: {target_page_id} ---")
            result = append_to_notion_page(target_page_id, content, self.notion_token)
            self.trajectory_steps.append({
                "step": step_number,
                "action": "tool_call",
                "tool": "append_to_notion_page",
                "args": {},
                "output": f"Appended content to Notion page ID: {target_page_id}"
            })
            return result
        except Exception as e:
            return self._handle_tool_error(step_number, "append_to_notion_page", str(e))
        
    def _execute_create_github_issue(self, repo_name, title, body, step_number=0):
        try:
            print(f"--- Agent is Creating GitHub Issue: {title} ---")
            result = create_github_issue(repo_name, title, body, self.github_token)
            self.trajectory_steps.append({
                "step": step_number,
                "action": "tool_call",
                "tool": "create_github_issue",
                "args": {"title": title},
                "output": result
            })
            return result
        except Exception as e:
            return self._handle_tool_error(step_number, "create_github_issue", str(e))
        
    def _execute_send_slack_message(self, message, step_number=0):
        try:
            print(f"--- Agent is Sending Slack Message ---")
            result = send_slack_message(message,self.webhook_url)
            self.trajectory_steps.append({
                "step": step_number,
                "action": "tool_call",
                "tool": "send_slack_message",
                "args": {},
                "output": result
            })
            return result
        except Exception as e:
            return self._handle_tool_error(step_number, "send_slack_message", str(e))
        
    def _handle_tool_error(self, step_number, tool_name, error_msg):
        """Helper to log errors consistently."""
        error_response = f"Error executing {tool_name}: {error_msg}"
        print(f"!!! {error_response}")
        self.trajectory_steps.append({
            "step": step_number,
            "action": "tool_call",
            "tool": tool_name,
            "error": error_msg
        })
        return error_response
        
    def run(self, question:  str) -> (str, list):
        """
        Execute agent loop.

        Returns: (final_answer, trajectory_steps)
        """
        self.question = question

        # Construct system message
        system_message = f"""You are a capable, goal-oriented autonomous AI assistant with GitHub and web access. Your goal is to satisfy the user's detailed instruction by applying the available tools systematically.

        Tools Available:
        1. Search: Use this tool to search the web for relevant information.
        2. Browse: Use this tool to visit a specific URL and extract detailed page content.
        3. List GitHub Directory: Use this tool to list files in a GitHub repository folder in a specific branch.
        4. Read GitHub File: Use this tool to read the content of a file from GitHub in a specific branch.
        5. Create GitHub Branch: Use this tool to create a new branch from a base branch in a GitHub repository.
        6. Create or Update GitHub File: Use this tool to create or update a file in a specific branch of a GitHub repository.
        7. Generate HTML Report: Use this tool to create an interactive HTML report summarizing your findings.
        8. Create Notion Page: Use this tool to create a new page in Notion with specified content.
        9. Append to Notion Page: Use this tool to append content to an existing Notion page.
        10. Create GitHub Issue: Use this tool to create a GitHub Issue to report bugs or request features.
        11. Send Slack Message: Use this tool to send a notification message to a Slack channel.

        CORE CODING CAPABILITIES:
        1. **Code Analysis**: Carefully examine repository files to understand structure and logic before editing.
        2. **Planning**: Summarize a concrete plan (files, improvements, tool calls) whenever the user request requires multi-step work.
        3. **Execution**: Apply the GitHub tools to implement edits, ensuring every `update_github_file` targets the prescribed branch and uses meaningful commit messages.
        4. **Reporting**: After edits, explain what changed, how it improves readability or efficiency, and how the user can verify the results.

        WORKFLOW:
        1. Understand and restate the user request, then plan the exact steps needed.
        2. Use exploratory tools (list/read) before editing so you know what to change.
        3. When editing, call the GitHub tools with the proper branch and arguments; describe each change in the conversation.
        4. After completing the edits, summarize which files were changed, what validation was run or suggested, and confirm the target branch contains the new commits.
        5. Only return a final answer when no more tool calls are needed; if the agent is finished, explain why the request is satisfied.
                
        IMPORTANT: When listing or reading GitHub files, ALWAYS specify the target branch to avoid confusion.
        """

        # Construct conversation
        self.conversation_history = [
            {"role": "system", "content": system_message},
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
                max_tokens=self.max_tokens,
                timeout=600
            )

            response_message = response.choices[0].message

            # Append full thought process
            if response_message.content:
                self.full_thought_process += f"\n--- Step {step+1} Thought ---\n{response_message.content}\n"

            # Update conversation
            self.conversation_history.append(response_message)

            # 2. Check if tool calls, execute one at a time
            if response_message.tool_calls:
                for tool_call in response_message.tool_calls:
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
                            error_response = self._handle_tool_error(
                                current_step_number, function_name, str(e)
                            )
                            self.conversation_history.append(
                                {
                                    "tool_call_id": tool_call.id,
                                    "role": "tool",
                                    "name": function_name,
                                    "content": error_response,
                                }
                            )
                    
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

                return final_answer, self.full_thought_process, self.trajectory_steps

        # 4. Maximum step reached
        print(f"--- Maximum agent step reached ---")

        # Fall back to baseline model
        force_answer_message = {
            "role": "user",
            "content": "You have reached the maximum number of search steps. Please synthesize the information you have gathered so far, or use your internal knowledge to provide the best possible answer to the original question."
        }
        self.conversation_history.append(force_answer_message)

        try:
            response = self.llm_client.chat.completions.create(
                model=self.model_name,
                messages=self.conversation_history,
                temperature=0.0,
                max_tokens=self.max_tokens,
                timeout=600
            )
            final_answer = response.choices[0].message.content

        except Exception as e:
            print(f"Error in final fallback: {e}")
            final_answer = "Error generating final answer."

        # Append trajectory steps
        self.trajectory_steps.append({
            "step": self.max_agent_steps,
            "action": "force_answer",
            "answer_raw": final_answer
        })

        self.full_thought_process += f"\n--- Step {step+1} Thought ---\n{final_answer}\n"

        return final_answer, self.full_thought_process, self.trajectory_steps

    