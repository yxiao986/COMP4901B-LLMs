import requests

def send_slack_message(message: str, webhook_url: str) -> str:
    """
    Sends a notification to Slack via Webhook.
    """
    if not webhook_url: return "Error: Slack Webhook URL missing."
    
    try:
        resp = requests.post(
            webhook_url, 
            json={"text": message},
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        if resp.status_code == 200:
            return "Success: Notification sent to Slack."
        return f"Error sending Slack message: {resp.status_code} - {resp.text}"
    except Exception as e:
        return f"Exception: {str(e)}"