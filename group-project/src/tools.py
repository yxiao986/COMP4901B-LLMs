from src.search import search

def get_tools_list() -> list[dict]:
    """
    Get the list of tools.
    """
    search_tool = {
        "type": "function",
        "function": {
            "name": "search",
            "description": "Search the web for information",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The query to search for"
                    }
                },
                "required": ["query"]
            }
        }       
    }
    
    return [search_tool]

def get_tool_by_name(name: str) -> dict:
    """
    Get the tool by name.
    """
    return get_tools_list()[name]

