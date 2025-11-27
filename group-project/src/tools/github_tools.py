
import requests
import base64
import json


def list_github_directory(repo_name: str, path: str, github_token: str) -> str:
    """
    Lists files in a GitHub repository directory.
    """
    if not github_token: return "Error: GitHub token is missing."

    path = path.strip("/")
    url = f"https://api.github.com/repos/{repo_name}/contents/{path}"
    headers = {"Authorization": f"token {github_token}", "Accept": "application/vnd.github.v3+json"}

    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return f"Error listing directory: {response.status_code} - {response.text}"
        
        items = response.json()
        if isinstance(items, dict):
            return f"Error: '{path}' is a file, not a directory."
        
        output = [f"--- Contents of {repo_name}/{path} ---"]
        for item in items:
            type_marker = "[DIR]" if item['type'] == 'dir' else "[FILE]"
            output.append(f"{type_marker} {item['name']}")
        return "\n".join(output)

    except Exception as e:
        return f"Exception: {str(e)}"

def read_github_file(repo_name: str, file_path: str, github_token: str) -> str:
    """
    Reads the content of a file from GitHub.
    """
    if not github_token: return "Error: GitHub token is missing."

    url = f"https://api.github.com/repos/{repo_name}/contents/{file_path}"
    headers = {"Authorization": f"token {github_token}", "Accept": "application/vnd.github.v3+json"}

    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return f"Error reading file: {response.status_code} - {response.text}"
        
        content = base64.b64decode(response.json()['content']).decode('utf-8')
        return f"--- Content of {file_path} ---\n{content}"

    except Exception as e:
        return f"Exception: {str(e)}"

def _get_branch_sha(repo_name: str, branch: str, token: str) -> str:
    """Internal Helper: Get SHA of a branch."""
    url = f"https://api.github.com/repos/{repo_name}/git/ref/heads/{branch}"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        return resp.json()['object']['sha']
    return None

def create_github_branch(repo_name: str, new_branch_name: str, base_branch: str, github_token: str) -> str:
    """
    Creates a new branch from a base branch (e.g. main).
    """
    if not github_token: return "Error: GitHub token is missing."

    # 1. Get SHA of base branch
    sha = _get_branch_sha(repo_name, base_branch, github_token)
    if not sha:
        return f"Error: Could not find base branch '{base_branch}'."

    # 2. Create new reference
    url = f"https://api.github.com/repos/{repo_name}/git/refs"
    headers = {"Authorization": f"token {github_token}", "Accept": "application/vnd.github.v3+json"}
    data = {
        "ref": f"refs/heads/{new_branch_name}",
        "sha": sha
    }

    try:
        resp = requests.post(url, headers=headers, json=data)
        if resp.status_code == 201:
            return f"Success: Branch '{new_branch_name}' created based on '{base_branch}'."
        elif resp.status_code == 422:
            return f"Error: Branch '{new_branch_name}' already exists."
        else:
            return f"Error creating branch: {resp.status_code} - {resp.text}"
    except Exception as e:
        return f"Exception: {str(e)}"

def create_or_update_file(repo_name: str, file_path: str, file_content: str, commit_message: str, branch_name: str, github_token: str) -> str:
    """
    Creates a new file or updates an existing one. This performs a COMMIT and PUSH automatically.
    """
    if not github_token: return "Error: GitHub token is missing."

    url = f"https://api.github.com/repos/{repo_name}/contents/{file_path}"
    headers = {"Authorization": f"token {github_token}", "Accept": "application/vnd.github.v3+json"}

    # Check if file exists to get SHA (needed for update)
    # We try to get the file info on the target branch
    sha = None
    try:
        get_resp = requests.get(f"{url}?ref={branch_name}", headers=headers)
        if get_resp.status_code == 200:
            sha = get_resp.json()['sha']
    except:
        pass

    # Prepare payload
    encoded_content = base64.b64encode(file_content.encode('utf-8')).decode('utf-8')
    data = {
        "message": commit_message,
        "content": encoded_content,
        "branch": branch_name
    }
    if sha:
        data["sha"] = sha # Required if updating an existing file

    try:
        resp = requests.put(url, headers=headers, json=data)
        if resp.status_code in [200, 201]:
            action = "updated" if sha else "created"
            return f"Success: File '{file_path}' {action} on branch '{branch_name}'. View at: {resp.json()['content']['html_url']}"
        else:
            return f"Error writing file: {resp.status_code} - {resp.text}"
    except Exception as e:
        return f"Exception: {str(e)}"