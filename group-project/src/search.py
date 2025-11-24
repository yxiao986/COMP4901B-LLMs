import requests
import json
from typing import List, Dict


def search(query: str, api_key: str, num_results: int = 3) -> List[Dict]:
    """
    Execute Google Search via Serper API.

    Args:
        query: Search query string
        api_key: Serper API key
        num_results: Number of search results to return (default: 3)
    
    Returns:
        List of dicts with 'title' and 'snippet' keys
    """
    if not api_key:
        raise ValueError("Serper api is required.")
    
    SERPER_API_URL = "https://google.serper.dev/search"

    headers = {
        "X-API-KEY": api_key,
        "Content-Type":"application/json"
    }

    request_body = {
        "q": query,
        "num": num_results
    }

    try:
        response = requests.post(
            SERPER_API_URL,
            headers=headers,
            json=request_body
        )

        response.raise_for_status()

        search_results = response.json()

        return search_results.get("organic",[])

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error: {http_err} - Response: {response.text}")
        return []

    except requests.exceptions.RequestException as req_err:
        print(f"Request error: {req_err}")
        return[]

    except json.JSONDecodeError:
        print(f"Failed to decode JSON reponse: {response.text}")

def format_search_results(results: List[Dict[str, str]]) -> str:
    """
    Format search results as a string for LLM consumption.
    
    Args:
        results: List of search result dicts with 'title' and 'snippet'
    
    Returns:
        Formatted string representation of search results
    """
    if not results:
        return "No search result."

    output_parts = ["Search results: \n"]

    for i, item in enumerate(results,1):
        title = item.get("title", "No title")
        snippet = item.get("snippet", "No snippet")
        link = item.get("link", "No link")

        output_parts.append(f"reuslt {i}")
        output_parts.append(f"  Title: {title}")
        output_parts.append(f"  Snippet: {snippet}")
        output_parts.append(f"  Source: {link}")

    return "\n".join(output_parts)