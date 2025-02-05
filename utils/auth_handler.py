import os
import sys
# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import logging
from utils.config import Config
import json
import traceback
import logging
import aiohttp

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def validate_credentials(username: str, token: str) -> bool:
    # Clean the token
    token = token.strip().strip('"').strip("'")
    
    # Handle dictionary format
    if token.startswith('{') and token.endswith('}'):
        token = token[1:-1]  # Remove { }
    
    # Handle warning message
    if token.startswith('_|WARNING:'):
        token = token.split('|_', 2)[-1]
    
    # Format token for Roblox API
    cookie_token = f"_|WARNING:-DO-NOT-SHARE-THIS.--Sharing-this-will-allow-someone-to-log-in-as-you-and-to-steal-your-ROBUX-and-items.|_{token}"
    
    headers = {
        'Cookie': f'.ROBLOSECURITY={cookie_token}',
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'User-Agent': 'Roblox/WinInet',
        'Referer': 'https://www.roblox.com/',
        'Origin': 'https://www.roblox.com',
        'X-CSRF-TOKEN': ''
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            # First, make a request to get the X-CSRF-TOKEN
            logger.info("Attempting to get CSRF token...")
            async with session.post(
                'https://auth.roblox.com/v2/login',
                headers=headers,
                ssl=True
            ) as response:
                logger.info(f"CSRF request status: {response.status}")
                logger.info(f"CSRF response headers: {dict(response.headers)}")
                
                csrf_token = response.headers.get('x-csrf-token')
                if csrf_token:
                    headers['X-CSRF-TOKEN'] = csrf_token
                    logger.info("Successfully obtained CSRF token")
                else:
                    logger.warning("No CSRF token received")

            # Now make the actual authentication request
            logger.info("Attempting authentication...")
            async with session.get(
                'https://users.roblox.com/v1/users/authenticated',
                headers=headers,
                ssl=True
            ) as response:
                response_text = await response.text()
                logger.info(f"Auth response status: {response.status}")
                logger.info(f"Auth response headers: {dict(response.headers)}")
                logger.info(f"Auth response body: {response_text}")

                if response.status != 200:
                    logger.error(f"Authentication failed with status {response.status}")
                    logger.error(f"Response headers: {dict(response.headers)}")
                    logger.error(f"Response body: {response_text}")
                    logger.error(f"Request headers used: {headers}")
                    return False
                    
                try:
                    data = await response.json()
                    logger.info(f"Parsed response data: {data}")
                    
                    if 'name' not in data:
                        logger.error("Response missing 'name' field")
                        logger.error(f"Full response data: {data}")
                        return False
                    
                    result = bool(data.get('name', '').lower() == username.lower())
                    logger.info(f"Username comparison: {data.get('name', '')} vs {username} = {result}")
                    return result
                    
                except json.JSONDecodeError as je:
                    logger.error(f"Failed to parse JSON response: {je}")
                    logger.error(f"Raw response: {response_text}")
                    return False
                
        except aiohttp.ClientError as ce:
            logger.error(f"Network error during validation: {ce}")
            logger.error(f"Request details: URL={session.base_url}, Headers={headers}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during validation: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            logger.error(f"Error traceback: {traceback.format_exc()}")
            return False
