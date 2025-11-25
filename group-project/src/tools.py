def get_tools_list() -> list[dict]:
    """
    Get the list of tools.
    """
    search_tool = {
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
    }

    browse_tool = {
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
    }

    return [search_tool, browse_tool]

def get_tool_by_name(name: str) -> dict:
    """
    Get the tool by name.
    """
    return get_tools_list()[name]

