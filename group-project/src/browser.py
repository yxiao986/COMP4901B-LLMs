from re import split
import requests
from bs4 import BeautifulSoup
from urllib3 import response

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
        