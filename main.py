import discord
from discord.ext import commands, tasks
import json
import logging
import aiohttp
from utils.auth_handler import validate_credentials
from utils.roblox_api import check_account_status
from utils.config import Config
import argparse
import sys
from discord.ext.commands import MissingRequiredArgument
import os
import traceback
import subprocess

import asyncio
import socket
import platform


# Load configuration
with open("config.json", "r") as f:
    config = json.load(f)

intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent
bot = commands.Bot(command_prefix="!", intents=intents)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Dictionary to store accounts
accounts = {}

@tasks.loop(minutes=5)
async def monitor_accounts():
    channel = bot.get_channel(config["log_channel_id"])
    if not channel:
        logging.error("Could not find log channel")
        return
        
    async with aiohttp.ClientSession() as session:
        for username, token in accounts.items():
            try:
                # Get user info
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json"
                }
                
                # First get user ID
                async with session.post(
                    "https://users.roblox.com/v1/usernames/users",
                    headers=headers,
                    json={"usernames": [username]}
                ) as user_response:
                    
                    if user_response.status == 401:
                        await channel.send(embed=discord.Embed(
                            title="Authorization Error",
                            description=f"Authorization invalid for account: {username}. Please update credentials.",
                            color=discord.Color.red()
                        ))
                        continue
                        
                    if user_response.status == 200:
                        user_data = await user_response.json()
                        users = user_data["data"]
                        
                        if not users:
                            await channel.send(embed=discord.Embed(
                                title="Account Not Found",
                                description=f"Account {username} not found.",
                                color=discord.Color.red()
                            ))
                            continue
                            
                        user_id = users[0]["id"]
                        
                        # Check moderation status
                        async with session.get(
                            f"https://users.roblox.com/v1/users/{user_id}",
                            headers=headers
                        ) as mod_response:
                            
                            if mod_response.status == 200:
                                mod_data = await mod_response.json()
                                is_banned = mod_data.get("isBanned", False)
                                
                                embed = discord.Embed(
                                    title="Account Status",
                                    description=f"Account: {username}",
                                    color=discord.Color.red() if is_banned else discord.Color.green()
                                )
                                embed.add_field(
                                    name="Status", 
                                    value="Banned" if is_banned else "Active"
                                )
                                await channel.send(embed=embed)
                            else:
                                logging.error(f"Error checking moderation status for {username}: {mod_response.status}")
                    
            except Exception as e:
                logging.error(f"Error monitoring account {username}: {e}")

@bot.event
async def on_ready():
    logger.info(f'Bot is ready. Logged in as {bot.user.name}')
    await validate_all_accounts()

async def validate_all_accounts():
    """Validate all accounts (main and additional)"""
    roblox_config = Config.get_roblox_config()
    additional_accounts = Config.get_additional_accounts()
    
    logger.info(f"Starting validation of all accounts (Main + {len(additional_accounts)} additional)")

    # Check main account
    is_valid = await validate_credentials(roblox_config['username'], roblox_config['token'])
    if is_valid:
        logger.info(f"✅ Main account validated: {roblox_config['username']}")
    else:
        logger.error(f"❌ Main account failed: {roblox_config['username']}")

    # Check additional accounts
    for username, token in additional_accounts.items():
        is_valid = await validate_credentials(username, token)
        if is_valid:
            logger.info(f"✅ Additional account validated: {username}")
        else:
            logger.error(f"❌ Additional account failed: {username}")

    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching, 
        name="Roblox accounts"
    ))
    monitor_accounts.start()

class AccountCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def add_account(self, ctx, username: str = None, token: str = None):
        """
        Add a Roblox account to the system
        Usage: !add_account <username> <token>
        """
        # Delete the message to protect sensitive info
        try:
            await ctx.message.delete()
        except:
            pass

        # Check if both parameters are provided
        if not username or not token:
            await ctx.send("❌ Please provide both username and token.\nUsage: `!add_account <username> <token>`")
            return

        try:
            # Clean the token (remove any quotes or extra spaces)
            token = token.strip().strip('"').strip("'")
            # If token includes warning message, extract just the token part
            if token.startswith('_|WARNING:'):
                token = token.split('|_', 2)[-1]
            
            # Validate the credentials
            is_valid = await validate_credentials(username, token)
            if is_valid:
                # Add to additional accounts in config
                additional_accounts = Config.get_additional_accounts()
                additional_accounts[username] = token
                if Config.save_additional_accounts(additional_accounts):
                    await ctx.send(f"✅ Successfully added account: {username}")
                    logger.info(f"New account added: {username}")
                    await list_accounts(ctx)  # Show updated list
                    return
                else:
                    await ctx.send("❌ Failed to save account.")
            else:
                await ctx.send("❌ Invalid credentials provided. Please check the username and token.")
                logger.warning(f"Failed to add account - invalid credentials: {username}")
        except Exception as e:
            logger.error(f"Error adding account: {str(e)}")
            await ctx.send("❌ An error occurred while adding the account.")

    @add_account.error
    async def add_account_error(self, ctx, error):
        if isinstance(error, MissingRequiredArgument):
            await ctx.send(f"❌ Missing required argument: {error.param.name}\nUsage: `!add_account <username> <token>`")

@bot.command()
async def list_accounts(ctx):
    """List all registered accounts"""
    try:
        # Force fresh data
        Config.save_additional_accounts(Config.get_additional_accounts())  # Refresh env
        roblox_config = Config.get_roblox_config()
        additional_accounts = Config.get_additional_accounts()
        
        logger.info(f"Listing accounts - Main: {roblox_config['username']}, Additional: {len(additional_accounts)}")
        account_list = []

        # Add main account
        if roblox_config['username'] and roblox_config['token']:
            is_valid = await validate_credentials(roblox_config['username'], roblox_config['token'])
            status = "✅" if is_valid else "❌"
            account_list.append(f"{status} {roblox_config['username']} (Main)")

        # Add additional accounts
        for username, token in additional_accounts.items():
            is_valid = await validate_credentials(username, token)
            status = "✅" if is_valid else "❌"
            account_list.append(f"{status} {username}")

        if account_list:
            formatted_list = "\n".join(account_list)
            await ctx.send(f"**Registered accounts:**\n{formatted_list}")
        else:
            await ctx.send("No accounts registered.")
            
    except Exception as e:
        logger.error(f"Error listing accounts: {str(e)}")
        await ctx.send("❌ An error occurred while listing accounts.")

@bot.command()
async def remove_account(ctx, username: str = None):
    """
    Remove a Roblox account from the system
    Usage: !remove_account <username>
    """
    if not username:
        await ctx.send("❌ Please provide a username.\nUsage: `!remove_account <username>`")
        return

    try:
        # Get both main and additional accounts
        roblox_config = Config.get_roblox_config()
        additional_accounts = Config.get_additional_accounts()
        logger.info(f"Attempting to remove account: {username}")
        logger.info(f"Current accounts: {list(additional_accounts.keys())}")

        # Check if trying to remove main account
        if username.lower() == roblox_config['username'].lower():
            await ctx.send("❌ Cannot remove main account. Update it in the .env file directly.")
            return

        # Check additional accounts (case-insensitive)
        account_found = False
        for acc_name in list(additional_accounts.keys()):
            if acc_name.lower() == username.lower():
                del additional_accounts[acc_name]
                logger.info(f"Removed account from dictionary: {acc_name}")
                
                # Save updated accounts
                if Config.save_additional_accounts(additional_accounts):
                    logger.info("Successfully saved updated accounts")
                    await ctx.send(f"✅ Successfully removed account: {acc_name}")
                    
                    # Force reload accounts and show updated list
                    additional_accounts = Config.get_additional_accounts()
                    logger.info(f"Updated accounts list: {list(additional_accounts.keys())}")
                    await list_accounts(ctx)
                    return
                else:
                    logger.error("Failed to save account changes")
                    await ctx.send("❌ Failed to save account changes.")
                    return

        if not account_found:
            logger.warning(f"Account not found: {username}")
            await ctx.send(f"❌ Account '{username}' not found.")
            
    except Exception as e:
        logger.error(f"Error removing account: {str(e)}")
        await ctx.send("❌ An error occurred while removing the account.")

@bot.command()
@commands.has_permissions(administrator=True)
async def restart(ctx):
    """Restart the bot (Admin only)"""
    try:
        await ctx.send("🔄 Restarting bot...")
        logger.info("Bot restart initiated by admin")
        
        # Get the Python executable path and script path
        python = sys.executable
        script = os.path.abspath(__file__)
        
        # Start new process before closing current
        subprocess.Popen([python, script])
        
        # Close the bot and exit
        await bot.close()
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Error during restart: {str(e)}")
        await ctx.send("❌ Failed to restart bot.")

@restart.error
async def restart_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You need administrator permissions to use this command.")

@bot.command()
async def validate(ctx):
    """Validate all accounts manually"""
    try:
        await ctx.send("🔄 Validating all accounts...")
        roblox_config = Config.get_roblox_config()
        additional_accounts = Config.get_additional_accounts()
        
        validation_results = []

        # Validate main account
        logger.info("Validating main account...")
        is_valid = await validate_credentials(roblox_config['username'], roblox_config['token'])
        status = "✅" if is_valid else "❌"
        validation_results.append(f"{status} {roblox_config['username']} (Main)")

        # Validate additional accounts
        if additional_accounts:
            logger.info(f"Validating {len(additional_accounts)} additional accounts...")
            for username, token in additional_accounts.items():
                is_valid = await validate_credentials(username, token)
                status = "✅" if is_valid else "❌"
                validation_results.append(f"{status} {username}")

        # Send validation results
        if validation_results:
            results = "\n".join(validation_results)
            await ctx.send(f"**Validation Results:**\n{results}")
        else:
            await ctx.send("No accounts found to validate.")

    except Exception as e:
        logger.error(f"Error during validation: {str(e)}")
        await ctx.send("❌ An error occurred during validation.")

def parse_arguments():
    parser = argparse.ArgumentParser(description='Roblox Account Manager')
    parser.add_argument('--check', action='store_true', help='Check account status')
    parser.add_argument('--validate', action='store_true', help='Validate credentials')
    parser.add_argument('--account', type=str, help='Specific account to check (from additional accounts)')
    return parser.parse_args()

def check_single_account(username, token, platform_config):
    """Check status for a single account"""
    logger.info(f"Processing account: {username}")
    
    if validate_credentials(username, token):
        status = check_account_status(
            platform="roblox",
            username=username,
            token=token,
            platform_config=platform_config
        )
        logger.info(f"Account {username} status: {status}")
        return True
    else:
        logger.error(f"Failed to validate credentials for account: {username}")
        return False

async def main():
    try:
        args = parse_arguments()
        
        # Load configurations
        roblox_config = Config.get_roblox_config()
        additional_accounts = Config.get_additional_accounts()

        # Handle specific account check
        if args.account:
            if args.account not in additional_accounts:
                logger.error(f"Account '{args.account}' not found in additional accounts")
                return
            token = additional_accounts[args.account]
            is_valid = await validate_credentials(args.account, token)
            if not is_valid:
                logger.error(f"Failed to validate credentials for account: {args.account}")
            else:
                logger.info(f"Successfully validated credentials for account: {args.account}")
            return

        # Check main account
        if args.check or args.validate:
            logger.info(f"Processing main account: {roblox_config['username']}")
            main_account_valid = await validate_credentials(
                roblox_config['username'],
                roblox_config['token']
            )
            
            if not main_account_valid:
                logger.error("Main account validation failed")
                return
            else:
                logger.info("Main account validation successful")

        # Process additional accounts
        if additional_accounts and not args.account:
            logger.info(f"Processing {len(additional_accounts)} additional accounts...")
            for username, token in additional_accounts.items():
                is_valid = await validate_credentials(username, token)
                if not is_valid:
                    logger.error(f"Failed to validate credentials for account: {username}")
                else:
                    logger.info(f"Successfully validated credentials for account: {username}")

    except KeyboardInterrupt:
        logger.error("Program terminated by user")
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        logger.error(traceback.format_exc())
        raise

async def setup():
    await bot.add_cog(AccountCommands(bot))

if __name__ == "__main__":
    try:
        # Load Discord token
        discord_token = Config.get_discord_token()
        
        # Configure asyncio and DNS
        if platform.system() == 'Windows':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            
            # Configure DNS for Windows
            socket.setdefaulttimeout(30)
            socket.getaddrinfo('discord.com', 443)  # Pre-resolve DNS
        
        # Start bot
        asyncio.run(main())
        asyncio.run(setup()) 
        bot.run(discord_token)
        
    except socket.gaierror:
        logger.error("DNS resolution failed. Please check your internet connection or DNS settings.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to start bot: {str(e)}")
        traceback.print_exc()