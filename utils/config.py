import os
import json
from dotenv import load_dotenv
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

class Config:
    @staticmethod
    def get_roblox_config():
        """Returns the Roblox API configuration"""
        # Force reload from .env
        load_dotenv(override=True)
        token = os.getenv('ROBLOX_TOKEN', '').strip().strip('"').strip("'")
        username = os.getenv('ROBLOX_USERNAME', '').strip()

        # If token includes warning message, extract just the token part
        if token.startswith('_|WARNING:'):
            token = token.split('|_', 2)[-1].rstrip('}')
            
        return {
            'token': token,
            'username': username
        }
    
    @staticmethod
    def get_additional_accounts():
        """Returns additional accounts if configured"""
        # Clear and reload environment variables
        os.environ.clear()
        load_dotenv(override=True)
        
        accounts = {}
        logger.info("Scanning for additional accounts...")
        
        # Get all environment variables
        for key, value in os.environ.items():
            if key.startswith('ROBLOX_ACCOUNT_'):
                username = key.replace('ROBLOX_ACCOUNT_', '')
                # Clean the token value
                token = value.strip().strip('"').strip("'")
                
                # Handle dictionary format
                if token.startswith('{') and token.endswith('}'):
                    token = token[1:-1]  # Remove { }
                
                # Handle warning message
                if token.startswith('_|WARNING:'):
                    token = token.split('|_', 2)[-1]
                
                accounts[username] = token.strip()
                logger.info(f"Found additional account: {username}")
        
        logger.info(f"Total additional accounts found: {len(accounts)}")
        return accounts
    
    @staticmethod
    def save_additional_accounts(accounts):
        """Saves the updated accounts dictionary"""
        try:
            # Load current .env content
            if os.path.exists('.env'):
                with open('.env', 'r') as f:
                    lines = [line for line in f.readlines() 
                            if not line.startswith('ROBLOX_ACCOUNT_')]
            else:
                lines = []

            # Add new accounts
            for username, token in accounts.items():
                lines.append(f'ROBLOX_ACCOUNT_{username}={token}\n')

            # Write back to .env
            with open('.env', 'w') as f:
                f.writelines(lines)

            # Force reload environment
            os.environ.clear()
            load_dotenv(override=True)
            
            return True
        except Exception as e:
            logger.error(f"Error saving accounts: {e}")
            return False

    @staticmethod
    def get_discord_token():
        """Returns Discord bot token from config.json"""
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
                return config.get('discord_bot_token', '')
        except Exception as e:
            logger.error(f"Error loading Discord token from config.json: {e}")
            return ''

    # ... rest of the Config class remains the same ... 
