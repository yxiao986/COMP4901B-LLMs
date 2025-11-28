def get_tools_list() -> list[dict]:
    """
    Get the list of tools.
    """
    return [{
        "type": "function",
        "function": {
            "name": "search",
            "description": "Search the web for information. Use this to find URLs and brief snippets.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query string."
                    }
                },
                "required": ["query"]
            }
        }       
    }, {
        "type": "function",
        "function": {
            "name": "browse",
            "description": "Visit a specific URL to read its full text content. Use this when search result snippets are truncated or lack sufficient detail.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL of the webpage to browse."
                    }
                },
                "required": ["url"]
            }
        }       
    },{
            "type": "function",
            "function": {
                "name": "list_github_directory",
                "description": "List files in a GitHub repository folder.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "repo_name": {"type": "string", "description": "e.g. 'owner/repo'"},
                        "path": {"type": "string", "description": "Folder path (empty for root)"},
                        "branch": {"type": "string", "description": "The branch to list files from (default: 'main')."}
                    },
                    "required": ["repo_name", "path"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "read_github_file",
                "description": "Read the content of a file from GitHub.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "repo_name": {"type": "string"},
                        "file_path": {"type": "string", "description": "Full path to the file"},
                        "branch": {"type": "string", "description": "The branch to read the file from (default: 'main')."}
                    },
                    "required": ["repo_name", "file_path"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "create_github_branch",
                "description": "Create a new branch to safely add test files.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "repo_name": {"type": "string"},
                        "new_branch_name": {"type": "string", "description": "Name of new branch (e.g. 'test/unit-tests')"},
                        "base_branch": {"type": "string", "description": "Usually 'main'"}
                    },
                    "required": ["repo_name", "new_branch_name", "base_branch"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "create_or_update_file",
                "description": "Create a new file (e.g. a test script) or update one. This acts as 'commit & push'.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "repo_name": {"type": "string"},
                        "file_path": {"type": "string", "description": "Path where the file should be created (e.g. 'tests/test_agent.py')"},
                        "file_content": {"type": "string", "description": "The python code content of the test file."},
                        "commit_message": {"type": "string", "description": "Git commit message (e.g. 'Add unit tests')"},
                        "branch_name": {"type": "string", "description": "The branch to push to."}
                    },
                    "required": ["repo_name", "file_path", "file_content", "commit_message", "branch_name"]
                }
            }
        },{
            "type": "function",
            "function": {
                "name": "generate_html_report",
                "description": "Generate a comprehensive, interactive documentation website (Javadoc-style). Supports sidebar navigation, search, and Mermaid diagrams.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filename": {
                            "type": "string", 
                            "description": "Output file path (e.g., 'docs/report.html')"
                        },
                        "title": {
                            "type": "string", 
                            "description": "The site/project title."
                        },
                        "pages": {
                            "type": "array",
                            "description": "List of documentation pages for the sidebar.",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string", "description": "Page title in sidebar."},
                                    "icon": {"type": "string", "description": "Bootstrap icon name (e.g., 'code-slash', 'diagram-3', 'book'). Optional."},
                                    "content": {"type": "string", "description": "Markdown content for this page. Supports code blocks and mermaid."}
                                },
                                "required": ["title", "content"]
                            }
                        }
                    },
                    "required": ["filename", "title", "pages"]
                }
            }
        },{
            "type": "function",
            "function": {
                "name": "create_notion_page",
                "description": "Create a NEW Notion page (document) inside the project folder. Returns the PAGE_ID of the new page.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Title of the new document"},
                        "content": {"type": "string", "description": "Initial content (Markdown)."}
                    },
                    "required": ["title", "content"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "append_to_notion_page",
                "description": "Append content to an EXISTING Notion page. You MUST provide the target_page_id returned by a previous 'create_notion_page' call.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "target_page_id": {
                            "type": "string", 
                            "description": "The specific Page ID (e.g., '1463b...'). You MUST get this ID from the output of a previous 'create_notion_page' tool call."
                        },
                        "content": {"type": "string", "description": "Markdown content to append."}
                    },
                    "required": ["target_page_id", "content"]
                }
            }
        },{
            "type": "function",
            "function": {
                "name": "create_github_issue",
                "description": "Create a GitHub Issue to report bugs or request features.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "repo_name": {"type": "string", "description": "Target repository (owner/repo)."},
                        "title": {"type": "string", "description": "Issue title."},
                        "body": {"type": "string", "description": "Detailed description of the issue."}
                    },
                    "required": ["repo_name", "title", "body"]
                }
            }
        },{
            "type": "function",
            "function": {
                "name": "send_slack_message",
                "description": "Send a notification to the team Slack channel.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "message": {"type": "string", "description": "The message content."}
                    },
                    "required": ["message"]
                }
            }
        }]

