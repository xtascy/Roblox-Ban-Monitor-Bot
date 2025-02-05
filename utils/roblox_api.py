import requests
from .config import Config

def check_account_status(platform, username=None, token=None, platform_config=None):
    """
    Checks the status of an account (e.g., banned, unbanned, invalid credentials).
    Returns "banned", "unbanned", or "invalid".
    """
    if platform_config is None:
        platform_config = Config.get_roblox_config()
    
    # Use provided credentials or fall back to config
    token = token or platform_config['token']
    username = username or platform_config['username']
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }
    
    response = requests.get(
        f"{platform_config['base_url']}/v1/usernames/users",
        headers=headers,
        json={"usernames": [username]}
    )
    
    # First verify the user exists and get their ID
    user_response = requests.get(
        f"https://users.roblox.com/v1/usernames/users",
        headers=headers,
        json={"usernames": [username]}
    )

    if user_response.status_code == 401:
        return "invalid"
    
    if user_response.status_code == 200:
        users = user_response.json()["data"]
        if not users:
            return "invalid"
            
        user_id = users[0]["id"]
        
        # Check moderation status using user ID
        mod_response = requests.get(
            f"https://users.roblox.com/v1/users/{user_id}",
            headers=headers
        )
        
        if mod_response.status_code == 200:
            data = mod_response.json()
            is_banned = data.get("isBanned", False)
            return "banned" if is_banned else "unbanned"
            
    raise Exception(f"Unexpected status code: {user_response.status_code}")
