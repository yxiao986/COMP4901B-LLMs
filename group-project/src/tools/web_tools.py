import requests
import json
from typing import List, Dict
import requests
from bs4 import BeautifulSoup



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


def browse(url:str) -> str:
    """
    Visit a web page URL and extract its main textual content.
    """
    # Use a generic User-Agent to avoid being blocked by simple anti-bot filters
    headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}

    try:
        # Visit URL
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')

        # Remove irrelevant elements
        for element in soup(["script", "style", "nav", "footer", "header", "noscript"]):
            element.extract()

        # Extract text
        text = soup.get_text()

        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split())
        cleaned_text = '\n'.join(chunk for chunk in chunks if chunk)

        # Truncate content
        max_length = 8000
        if len(cleaned_text) > max_length:
            cleaned_text = cleaned_text[:max_length] + "\n\n...[Content Truncated due to length]..."

        return cleaned_text

    except requests.exceptions.RequestException as e:
        return f"Error browsing {url}: {str(e)}"

    except Exception as e:
        return f"Error processing content from {url}: {str(e)}"
        