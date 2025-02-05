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
                        
                        # Check moderation status with detailed ban info
                        async with session.get(
                            f"https://users.roblox.com/v1/users/{user_id}",
                            headers=headers
                        ) as mod_response:
                            
                            if mod_response.status == 200:
                                mod_data = await mod_response.json()
                                is_banned = mod_data.get("isBanned", False)
                                
                                if is_banned:
                                    # Get detailed ban information
                                    async with session.get(
                                        f"https://accountsettings.roblox.com/v1/users/{user_id}/ban-status",
                                        headers=headers
                                    ) as ban_response:
                                        if ban_response.status == 200:
                                            ban_data = await ban_response.json()
                                            
                                            embed = discord.Embed(
                                                title="Got banned!",
                                                description=f"Account: {username}",
                                                color=discord.Color.red()
                                            )
                                            
                                            # Add ban details
                                            if "banEndDate" in ban_data:
                                                embed.add_field(
                                                    name="Ban Length",
                                                    value=ban_data.get("banDuration", "Unknown"),
                                                    inline=True
                                                )
                                                embed.add_field(
                                                    name="Ban Ends",
                                                    value=ban_data.get("banEndDate", "Unknown"),
                                                    inline=True
                                                )
                                            
                                            # Add game/place info if available
                                            if "bannedFromPlace" in ban_data and ban_data["bannedFromPlace"]:
                                                embed.add_field(
                                                    name="Banned From",
                                                    value=f"Place ID: {ban_data['bannedFromPlace']}",
                                                    inline=False
                                                )
                                            
                                            # Add reason if available
                                            if "reasonText" in ban_data:
                                                embed.add_field(
                                                    name="Reason",
                                                    value=ban_data.get("reasonText", "No reason provided"),
                                                    inline=False
                                                )
                                            
                                            await channel.send(embed=embed)
                                else:
                                    # Account is not banned, you might want to log this or handle differently
                                    pass
                            else:
                                logging.error(f"Error checking moderation status for {username}: {mod_response.status}")
                    
            except Exception as e:
                logging.error(f"Error monitoring account {username}: {e}")

@bot.event
async def on_ready():
    logger.info(f'Bot is ready. Logged in as {bot.user.name}')
    await validate_all_accounts()
    
    # Clear screen after validation
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # Show welcome message
    print("""
╔════════════════════════════════════════╗
║         Welcome to Account Panel       ║
╚════════════════════════════════════════╝
""")
    
    # Show account status
    roblox_config = Config.get_roblox_config()
    additional_accounts = Config.get_additional_accounts()
    
    print(f"Monitoring {len(additional_accounts) + 1} account(s):")
    print(f"• Main: {roblox_config['username']}")
    for username in additional_accounts.keys():
        print(f"• Alt: {username}")
    
    print("\nAvailable Commands:")
    print("!help           - Show help message")
    print("!list_accounts  - Show all monitored accounts")
    print("!add_account    - Add a new account")
    print("!remove_account - Remove an account")
    print("!validate       - Check all accounts")
    print("!bancheck       - Check if a user is banned")
    print("!restart        - Restart the bot (Admin only)")
    
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching, 
        name="Roblox accounts"
    ))
    monitor_accounts.start()

@bot.command(name='help')
async def help_command(ctx):
    """Show help information"""
    embed = discord.Embed(
        title="Account Panel Help",
        description="Available Commands:",
        color=discord.Color.blue()
    )
    
    commands = {
        "!help": "Show this help message",
        "!list_accounts": "Show all monitored accounts",
        "!add_account": "Add a new account\nUsage: !add_account username token",
        "!remove_account": "Remove an account\nUsage: !remove_account username",
        "!validate": "Check all accounts",
        "!bancheck": "Check if a user is banned\nUsage: !bancheck username",
        "!restart": "Restart the bot (Admin only)"
    }
    
    for cmd, desc in commands.items():
        embed.add_field(name=cmd, value=desc, inline=False)
    
    await ctx.send(embed=embed)

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
            embed = discord.Embed(
                title="❌ Error",
                description="Please provide both username and token.\nUsage: `!add_account <username> <token>`",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
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
                    embed = discord.Embed(
                        title="✅ Success",
                        description=f"Successfully added account: {username}",
                        color=discord.Color.green()
                    )
                    await ctx.send(embed=embed)
                    logger.info(f"New account added: {username}")
                    await list_accounts(ctx)
                    return
                else:
                    embed = discord.Embed(
                        title="❌ Error",
                        description="Failed to save account.",
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=embed)
            else:
                embed = discord.Embed(
                    title="❌ Error",
                    description="Invalid credentials provided. Please check the username and token.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                logger.warning(f"Failed to add account - invalid credentials: {username}")
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description="An error occurred while adding the account.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @add_account.error
    async def add_account_error(self, ctx, error):
        if isinstance(error, MissingRequiredArgument):
            embed = discord.Embed(
                title="❌ Error",
                description=f"Missing required argument: {error.param.name}\nUsage: `!add_account <username> <token>`",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

@bot.command()
async def list_accounts(ctx):
    """List all registered accounts with ban status"""
    try:
        # Force fresh data
        Config.save_additional_accounts(Config.get_additional_accounts())
        roblox_config = Config.get_roblox_config()
        additional_accounts = Config.get_additional_accounts()
        
        logger.info(f"Listing accounts - Main: {roblox_config['username']}, Additional: {len(additional_accounts)}")
        account_list = []

        async with aiohttp.ClientSession() as session:
            # Check main account
            if roblox_config['username'] and roblox_config['token']:
                is_valid = await validate_credentials(roblox_config['username'], roblox_config['token'])
                status = "✅" if is_valid else "❌"
                
                # Check ban status if valid
                ban_status = "Unknown"
                if is_valid:
                    headers = {"Authorization": f"Bearer {roblox_config['token']}", "Accept": "application/json"}
                    async with session.post(
                        "https://users.roblox.com/v1/usernames/users",
                        headers=headers,
                        json={"usernames": [roblox_config['username']]}
                    ) as response:
                        if response.status == 200:
                            user_data = await response.json()
                            if user_data["data"]:
                                user_id = user_data["data"][0]["id"]
                                async with session.get(
                                    f"https://users.roblox.com/v1/users/{user_id}",
                                    headers=headers
                                ) as mod_response:
                                    if mod_response.status == 200:
                                        mod_data = await mod_response.json()
                                        ban_status = "🚫 Banned" if mod_data.get("isBanned", False) else "✅ Active"
                
                account_list.append(f"{status} {roblox_config['username']} (Main) - {ban_status}")

            # Check additional accounts
            for username, token in additional_accounts.items():
                is_valid = await validate_credentials(username, token)
                status = "✅" if is_valid else "❌"
                
                # Check ban status if valid
                ban_status = "Unknown"
                if is_valid:
                    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
                    async with session.post(
                        "https://users.roblox.com/v1/usernames/users",
                        headers=headers,
                        json={"usernames": [username]}
                    ) as response:
                        if response.status == 200:
                            user_data = await response.json()
                            if user_data["data"]:
                                user_id = user_data["data"][0]["id"]
                                async with session.get(
                                    f"https://users.roblox.com/v1/users/{user_id}",
                                    headers=headers
                                ) as mod_response:
                                    if mod_response.status == 200:
                                        mod_data = await mod_response.json()
                                        ban_status = "🚫 Banned" if mod_data.get("isBanned", False) else "✅ Active"
                
                account_list.append(f"{status} {username} - {ban_status}")

        if account_list:
            formatted_list = "\n".join(account_list)
            embed = discord.Embed(
                title="Registered Accounts",
                description=formatted_list,
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
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
        embed = discord.Embed(
            title="❌ Error",
            description="Please provide a username.\nUsage: `!remove_account <username>`",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    try:
        # Get both main and additional accounts
        roblox_config = Config.get_roblox_config()
        additional_accounts = Config.get_additional_accounts()
        logger.info(f"Attempting to remove account: {username}")
        logger.info(f"Current accounts: {list(additional_accounts.keys())}")

        # Check if trying to remove main account
        if username.lower() == roblox_config['username'].lower():
            embed = discord.Embed(
                title="❌ Error",
                description="Cannot remove main account. Update it in the .env file directly.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
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
                    embed = discord.Embed(
                        title="✅ Success",
                        description=f"Successfully removed account: {acc_name}",
                        color=discord.Color.green()
                    )
                    await ctx.send(embed=embed)
                    
                    # Force reload accounts and show updated list
                    additional_accounts = Config.get_additional_accounts()
                    logger.info(f"Updated accounts list: {list(additional_accounts.keys())}")
                    await list_accounts(ctx)
                    return
                else:
                    logger.error("Failed to save account changes")
                    embed = discord.Embed(
                        title="❌ Error",
                        description="Failed to save account changes.",
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=embed)
                    return

        if not account_found:
            logger.warning(f"Account not found: {username}")
            embed = discord.Embed(
                title="❌ Error",
                description=f"Account '{username}' not found.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            
    except Exception as e:
        logger.error(f"Error removing account: {str(e)}")
        embed = discord.Embed(
            title="❌ Error",
            description="An error occurred while removing the account.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def restart(ctx):
    """Restart the bot (Admin only)"""
    try:
        embed = discord.Embed(
            title="🔄 Restarting",
            description="Bot is restarting...",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)
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
        embed = discord.Embed(
            title="❌ Error",
            description="Failed to restart bot.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

@restart.error
async def restart_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(
            title="❌ Error",
            description="You need administrator permissions to use this command.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

@bot.command()
async def validate(ctx):
    """Validate all accounts manually"""
    try:
        embed = discord.Embed(
            title="🔄 Validation Started",
            description="Validating all accounts...",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)
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
            embed = discord.Embed(
                title="Validation Results",
                description=results,
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="No Accounts",
                description="No accounts found to validate.",
                color=discord.Color.yellow()
            )
            await ctx.send(embed=embed)

    except Exception as e:
        logger.error(f"Error during validation: {str(e)}")
        embed = discord.Embed(
            title="❌ Error",
            description="An error occurred during validation.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

@bot.command(aliases=['bancheck', 'checkstatus', 'checkban'])
async def check_ban(ctx, username: str = None):
    """Check ban status for a Roblox user"""
    if not username:
        embed = discord.Embed(
            title="❌ Error",
            description="Please provide a username.\nUsage: `!checkban <username>`",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    try:
        async with aiohttp.ClientSession() as session:
            # First get user ID
            async with session.post(
                "https://users.roblox.com/v1/usernames/users",
                json={"usernames": [username]}
            ) as response:
                if response.status == 200:
                    user_data = await response.json()
                    users = user_data["data"]
                    
                    if not users:
                        embed = discord.Embed(
                            title="User Not Found",
                            description=f"Could not find user: {username}",
                            color=discord.Color.red()
                        )
                        await ctx.send(embed=embed)
                        return
                        
                    user_id = users[0]["id"]
                    
                    # Check moderation status
                    async with session.get(
                        f"https://users.roblox.com/v1/users/{user_id}"
                    ) as mod_response:
                        if mod_response.status == 200:
                            mod_data = await mod_response.json()
                            is_banned = mod_data.get("isBanned", False)
                            
                            if is_banned:
                                embed = discord.Embed(
                                    title="Ban Status",
                                    description=f"User: {username}",
                                    color=discord.Color.red()
                                )
                                embed.add_field(
                                    name="Status",
                                    value="🚫 Banned",
                                    inline=False
                                )
                                
                                # Add appeal information if configured
                                if "appeal_url" in config:
                                    embed.add_field(
                                        name="Appeal Information",
                                        value=f"To appeal this ban, visit: {config['appeal_url']}",
                                        inline=False
                                    )
                                    
                                    # Notify moderators about potential appeal
                                    if "mod_role_id" in config:
                                        mod_role = ctx.guild.get_role(config["mod_role_id"])
                                        if mod_role:
                                            appeal_embed = discord.Embed(
                                                title="Ban Appeal Available",
                                                description=f"Ban appeal available for {username}. Please review.",
                                                color=discord.Color.blue()
                                            )
                                            await ctx.send(content=mod_role.mention, embed=appeal_embed)
                            else:
                                embed = discord.Embed(
                                    title="Ban Status",
                                    description=f"User: {username}",
                                    color=discord.Color.green()
                                )
                                embed.add_field(
                                    name="Status",
                                    value="✅ Not Banned",
                                    inline=False
                                )
                            
                            # Send result as DM if configured
                            if "private_ban_checks" in config and config["private_ban_checks"]:
                                try:
                                    await ctx.author.send(embed=embed)
                                    await ctx.message.add_reaction('✅')
                                except discord.Forbidden:
                                    await ctx.send("❌ Could not send DM. Please enable DMs from server members.")
                            else:
                                await ctx.send(embed=embed)
                                
    except Exception as e:
        logger.error(f"Error checking ban status: {str(e)}")
        embed = discord.Embed(
            title="❌ Error",
            description="An error occurred while checking ban status.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

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
