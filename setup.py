import os
import json
import getpass

def create_config():
    print("\n=== Discord Bot Configuration ===")
    print("Please follow these steps to configure your bot:")
    
    # Get Discord configuration
    print("\n1. Discord Bot Setup:")
    print("   - Go to https://discord.com/developers/applications")
    print("   - Create a New Application")
    print("   - Go to Bot section and create a bot")
    print("   - Copy the bot token")
    token = getpass.getpass("Enter your Discord bot token: ")
    
    print("\n2. Discord Channel Setup:")
    print("   - Right-click the channel you want to use for logs")
    print("   - Click 'Copy ID' (Enable Developer Mode if not visible)")
    channel_id = input("Enter the log channel ID: ")
    
    # Create config.json
    config = {
        "discord_bot_token": token,
        "log_channel_id": int(channel_id),
        "private_ban_checks": False
    }
    
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=4)
    print("\n✅ config.json created successfully!")

def create_env():
    print("\n=== Roblox Account Configuration ===")
    print("\n3. Main Roblox Account Setup:")
    print("   - Go to Roblox and log into your main account")
    print("   - Press F12 to open Developer Tools")
    print("   - Go to Application > Cookies > .ROBLOSECURITY")
    print("   - Copy the cookie value")
    
    main_token = getpass.getpass("Enter your main account's .ROBLOSECURITY token: ")
    main_username = input("Enter your main account's username: ")
    
    # Create .env file
    env_content = [
        "# Main Roblox Account",
        f"ROBLOX_TOKEN={main_token}",
        f"ROBLOX_USERNAME={main_username}",
        "",
        "# Additional Accounts (Optional)",
        "# Format: ROBLOX_ACCOUNT_username=token"
    ]
    
    with open('.env', 'w') as f:
        f.write('\n'.join(env_content))
    print("\n✅ .env file created successfully!")

def add_additional_accounts():
    print("\n4. Additional Accounts (Optional):")
    while True:
        add_another = input("\nWould you like to add another account? (y/n): ").lower()
        if add_another != 'y':
            break
            
        username = input("Enter account username: ")
        token = getpass.getpass("Enter account .ROBLOSECURITY token: ")
        
        with open('.env', 'a') as f:
            f.write(f"\nROBLOX_ACCOUNT_{username}={token}")
        print("✅ Account added successfully!")

def main():
    print("""
╔════════════════════════════════════════╗
║     Roblox Account Monitor Setup       ║
╚════════════════════════════════════════╝
    """)
    
    # Check if files already exist
    if os.path.exists('config.json') or os.path.exists('.env'):
        overwrite = input("Existing configuration found. Overwrite? (y/n): ").lower()
        if overwrite != 'y':
            print("Setup cancelled.")
            return
    
    try:
        create_config()
        create_env()
        add_additional_accounts()
        
        print("""
\n✨ Setup Complete! ✨
To start the bot, run: python main.py

Available commands:
!list_accounts - Show all monitored accounts
!add_account - Add a new account
!remove_account - Remove an account
!validate - Check all accounts
!restart - Restart the bot (Admin only)
        """)
        
    except Exception as e:
        print(f"\n❌ Error during setup: {str(e)}")
        print("Please try again or set up the files manually.")

if __name__ == "__main__":
    main() 